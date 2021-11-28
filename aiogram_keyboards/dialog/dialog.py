from typing import Type, Optional, Union, Callable, Awaitable, TypeVar
from dataclasses import dataclass


from aiogram import Dispatcher
from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher.filters.builtin import StateFilter

from ..keyboard import Keyboard
from ..button import Button
from ..dialog.convert import ConvertTelegramObj
from ..configuration import get_dp
from ..utils import _hash_text


class ButtonActions:
    SKIP = 'skip'


T = TypeVar('T')


@dataclass
class State:
    dialog: Type['Dialog']
    name: str
    convertor: Union[Type[ConvertTelegramObj], ConvertTelegramObj]
    keyboard: Optional[Type[Keyboard]]

    def __repr__(self):
        if self.is_finished:
            status = 'Finished'
        else:
            status = 'Processing'

        return f'<{status} State "{self.name}">'

    @property
    def is_finished(self) -> bool:
        if isinstance(self.convertor, type):
            result = False
        elif isinstance(self.convertor, ConvertTelegramObj):
            result = True
        else:
            raise RuntimeError()

        return result

    def hex_hash(self):
        """
        Get dialog current state hash
        """

        dialog_hash = self.dialog.hex_hash()
        result = dialog_hash + _hash_text(f'::state-{self.name}::')

        return _hash_text(result)


telegram_object = Union[Message, CallbackQuery]
telegram_handler = Callable[[telegram_object], Awaitable[None]]


class Dialog:
    """
    Dialogs constructor
    """

    _all_states: list[State] = []

    @classmethod
    def hex_hash(cls):
        """
        Get dialog hash
        """

        result = ''

        for i in cls._all_states:
            for button in i.keyboard.get_choices():
                result += button.hex_hash()

        result = _hash_text(result)

        return result

    @classmethod
    def __hash__(cls) -> int:
        return int(cls.hex_hash(), base=16)

    def __init_subclass__(cls, **kwargs):
        for var_name, annotation in cls.__annotations__.items():
            if issubclass(annotation, ConvertTelegramObj):
                try:
                    var = cls.__dict__[var_name]
                except KeyError:
                    var = None

                if isinstance(var, str):
                    def create_kb(text: str):
                        class KB(Keyboard):
                            __text__ = text
                        return KB

                    var = create_kb(var)

                def set_ignore_state(kb: Type[Keyboard], ignore_state: bool) -> Type[Keyboard]:
                    for i in kb.get_choices():
                        i.ignore_state = ignore_state

                    return kb

                var = set_ignore_state(var, False)

                state = State(cls, var_name, annotation, var)
                cls._all_states.append(state)

    def __init__(self, dp: Dispatcher, chat_id: int, user_id: int = None):

        if user_id is None:
            user_id = chat_id

        self._dp = dp

        self.chat_id = chat_id
        self.user_id = user_id

        self._current_id: int = 0

        self._registered_handlers: list = []

    def _set_handlers(self, on_finish: telegram_handler = None):
        if on_finish is None:
            async def default_on_finish(*_args, **_kwargs):
                pass

            on_finish = default_on_finish

        for i in self._all_states:
            handler = self._handler_factory(i, on_finish=on_finish)
            self._dp.message_handlers.register(handler, filters=[StateFilter(self._dp, i.hex_hash())])
            self._registered_handlers.append(handler)

    def _remove_handlers(self):
        for i in self._registered_handlers:
            self._dp.message_handlers.unregister(i)

        self._registered_handlers.clear()

    async def _first(self) -> State:
        """
        Reset iteration
        """

        self._current_id = 0

        await self._set_current_state()

        return await self._fetch()

    async def _next(self) -> State:
        """
        Next state
        """

        self._current_id += 1

        await self._set_current_state()

        return await self._fetch()

    async def _previous(self) -> State:
        """
        Previous state
        """

        self._current_id -= 1

        await self._set_current_state()

        return await self._fetch()

    async def _fetch(self) -> State:
        """
        Get state
        """

        try:
            return self._all_states[self._current_id]
        except IndexError:
            raise StopIteration

    async def _finish(self) -> None:
        """
        Finish dialog
        """

        state = self._dp.current_state(chat=self.chat_id, user=self.user_id)
        await state.finish()

        self._remove_handlers()

        return None

    async def _set_current_state(self):
        """
        Set current dialog state for chat in aiogram
        """

        state = self._dp.current_state(chat=self.chat_id, user=self.user_id)
        current_state = await self._fetch()

        await state.set_state(current_state.hex_hash())

        return None

    async def process(self, on_finish: Callable[[T], Awaitable[None]]):
        """Process dialog

        Start dialog, on finish - call `on_finish` with results.
        Method register all handlers with state and custom filters

        """

        self._set_handlers(on_finish)

        await self._first()
        current = await self._fetch()

        await current.keyboard.process(self.chat_id)

    def _handler_factory(self,
                         state: State,
                         on_finish: Callable[['Dialog'], Awaitable[None]]
                         ) -> Callable[[telegram_object], Awaitable[None]]:

        async def handler(obj: Union[Message, CallbackQuery]):
            button = Button.from_telegram_object(obj)

            async def read_value():
                try:
                    state.convertor = state.convertor(obj)
                except ValueError:
                    # keep wait for normal input
                    await self._previous()

            if button is not None:
                if button.action == ButtonActions.SKIP:
                    state.convertor = state.convertor(None)
                else:
                    await read_value()
            else:
                await read_value()

            try:
                await self._next()
            except RuntimeError:

                # HOW HANDLE COROUTINE EX?
                # Here we must handle StopIteration
                # TODO: Fix it!

                self._sync_cls_states()

                await self._finish()
                await on_finish(self)
            else:
                current = await self._fetch()

                await current.keyboard.process(self.chat_id)

        return handler

    def _sync_cls_states(self):
        """Sync cls states method

        Synchronize self._all_states with cls variables
        Call it to set states results to cls

        """

        for i in self._all_states:
            self.__dict__[i.name] = i.convertor

    @classmethod
    def entry_point(cls, *filters, commands: list[str] = None) -> Callable:
        """
        Set entry point for dialog
        """

        filters = list(filters)

        for num, i in enumerate(filters):
            if isinstance(i, Button):
                filters[num] = i.filter()

        if commands is None:
            commands = []

        dp = get_dp()

        def decorator(func):

            async def call_dialog(obj: telegram_object, **_kwargs):
                if isinstance(obj, Message):
                    chat = obj.chat
                elif isinstance(obj, CallbackQuery):
                    chat = obj.message.chat
                else:
                    raise NotImplementedError(f'Handle of object `{obj}` in dialog not implemented')

                self = cls(dp, chat.id)

                await self.process(func)

            dp.register_message_handler(call_dialog, *filters, commands=commands)
            dp.register_callback_query_handler(call_dialog, *filters)

            return func

        return decorator

    def __repr__(self):
        return repr(self._all_states)

    __str__ = __repr__

    def to_dict(self):
        result = dict()

        for i in self._all_states:
            result.update({i.name: i.convertor.result})

        return result

    async def answer(self, text: str):
        result = await self._dp.bot.send_message(self.chat_id, text=text)

        return result
