from typing import Type, Optional, Union, Callable, Awaitable, TypeVar

from aiogram import Dispatcher
from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher.filters.builtin import StateFilter

from ..keyboard import Keyboard
from ..button import Button
from ..dialog.cast import CastTelegramObj
from ..configuration import get_dp
from ..utils import _hash_text

from .state import State


T = TypeVar('T')


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
            if issubclass(annotation, CastTelegramObj):
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

                state = State(var_name, annotation, var)
                cls._all_states.append(state)

    def __init__(self, dp: Dispatcher, chat_id: int, user_id: int = None):

        if user_id is None:
            user_id = chat_id

        self.core = DialogCore(dp, chat_id, user_id, self._all_states)

    async def process(self, on_finish: Callable[[T], Awaitable[None]]):
        """Process dialog

        Start dialog, on finish - call `on_finish` with results.
        Method register all handlers with state and custom filters

        """

        on_finish = self._update_finish_handler(on_finish)
        await self.core.setup_dialog(on_finish)

        current = self.core.current
        await current.keyboard.process(self.core.chat_id)

    def _update_finish_handler(self,
                               handler: Callable[['Dialog'], Awaitable[None]]) -> Callable[[], Awaitable[None]]:

        async def new_handler():
            self._sync_cls_states()
            await handler(self)

        return new_handler

    def _sync_cls_states(self):
        """Sync cls states method

        Synchronize core states with this cls variables
        Call it to set states results to cls

        """

        for i in self.core.states:
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
            result.update({i.name: i.result})

        return result

    async def answer(self, text: str):
        result = await self.core.dp.bot.send_message(self.core.chat_id, text=text)

        return result


class DialogCore:
    def __init__(self,
                 dp: Dispatcher,
                 chat_id: int,
                 user_id: int,
                 states: list[State]):

        self.dp: Dispatcher = dp

        self.states = self._connect_states(states)

        self.chat_id = chat_id
        self.user_id = user_id

        self._registered_handlers = []
        self._current_step_id = 0

    def _connect_states(self, states: list[State]) -> list[State]:
        """
        Provide DialogCore object to states
        """

        for i in states:
            i.connect_dialog(self)

        return states

    @property
    def current(self) -> State:
        """
        Get current dialog state
        """

        result = self.states[self._current_step_id]

        return result

    async def next(self, step: int = 1) -> State:
        """
        Next dialog state
        """

        self._current_step_id += step

        try:
            await self.current.set()
        except IndexError as e:
            self._current_step_id -= step
            raise e

        return self.current

    async def previous(self, step: int = 1) -> State:
        """
        Previous dialog state
        """

        self._current_step_id -= step
        await self.current.set()

        return self.current

    async def first(self):
        """
        Set first dialog state
        """

        self._current_step_id = 0
        await self.current.set()

        return self.current

    def _handler_factory(self,
                         state: State,
                         on_finish: Callable[[], Awaitable[None]]
                         ) -> Callable[[telegram_object], Awaitable[None]]:

        async def handler(obj: Union[Message, CallbackQuery]):

            button = Button.from_telegram_object(obj)

            async def read_value():
                try:
                    state.set_result(obj)
                except ValueError:
                    # keep wait for normal input
                    await self.previous(step=1)

            if button is not None:
                if button.action is not None:
                    await button.action(self).process(obj)
            else:
                await read_value()

            try:
                await self.next()
            except IndexError:

                await self.finish()
                await on_finish()
            else:
                current = self.current

                await current.keyboard.process(self.chat_id)

        return handler

    async def finish(self) -> None:
        """
        Finish dialog
        """

        state = self.dp.current_state(chat=self.chat_id, user=self.user_id)
        await state.finish()

        self.remove_handlers()

        return None

    async def setup_dialog(self, on_finish: Callable[[], Awaitable[None]] = None):
        if on_finish is None:
            async def default_on_finish(*_args, **_kwargs):
                pass

            on_finish = default_on_finish

        for i in self.states:
            handler = self._handler_factory(i, on_finish=on_finish)
            self.dp.message_handlers.register(handler, filters=[StateFilter(self.dp, i.hex_hash())])
            self._registered_handlers.append(handler)

        await self.first()

    def remove_handlers(self):
        for i in self._registered_handlers:
            self.dp.message_handlers.unregister(i)

        self._registered_handlers.clear()

    def hex_hash(self):
        """
        Get dialog hash
        """

        result = ''

        for i in self.states:
            for button in i.keyboard.get_choices():
                result += button.hex_hash()

        result = _hash_text(result)

        return result
