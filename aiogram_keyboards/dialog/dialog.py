from typing import Type, Optional, Union, Callable, Awaitable, TypeVar
from dataclasses import dataclass


from aiogram import Dispatcher
from aiogram.types import CallbackQuery, Message

from ..keyboard import Keyboard
from ..button import Button
from ..dialog.convert import ConvertTelegramObj
from ..configuration import get_dp


class ButtonActions:
    SKIP = 'skip'


T = TypeVar('T')


@dataclass
class State:
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
        if self.convertor == ConvertTelegramObj:
            result = False
        elif isinstance(self.convertor, ConvertTelegramObj):
            result = True
        else:
            raise RuntimeError()

        return result


telegram_object = Union[Message, CallbackQuery]
telegram_handler = Callable[[telegram_object], Awaitable[None]]


class Dialog:
    """
    Dialogs constructor
    """

    _all_states: list[State] = []

    def __init_subclass__(cls, **kwargs):
        for var_name, annotation in cls.__annotations__.items():
            if issubclass(annotation, ConvertTelegramObj):
                try:
                    var = cls.__dict__[var_name]
                except KeyError:
                    var = None

                if isinstance(var, str):
                    var = Keyboard(var)

                state = State(var_name, annotation, var)
                cls._all_states.append(state)

    def __init__(self, dp: Dispatcher, chat_id: int):
        self._dp = dp
        self._chat_id = chat_id

        self._current_id: int = 0

    def _first(self) -> State:
        """
        Reset iteration
        """

        self._current_id = 0

        return self._fetch()

    def _next(self) -> State:
        """
        Next state
        """

        self._current_id += 1

        return self._fetch()

    def _previous(self) -> State:
        """
        Previous state
        """

        self._current_id -= 1

        return self._fetch()

    def _fetch(self) -> State:
        """
        Get state
        """

        try:
            return self._all_states[self._current_id]
        except IndexError:
            raise StopIteration

    async def process(self: T, on_finish: Callable[[T], Awaitable[None]]):
        """Process dialog

        Start dialog, on finish - call `on_finish` with results

        """

        current = self._fetch()
        handler = self._handler_factory(current, on_finish)
        self._dp.message_handlers.register(handler, current.keyboard.filter())

        await current.keyboard.process(self._chat_id)

    def _handler_factory(self,
                         state: State,
                         on_finish: Callable[[T], Awaitable[None]]) -> Callable[[telegram_object], Awaitable[None]]:

        async def handler(obj: Union[Message, CallbackQuery]):
            button = Button.from_telegram_object(obj)

            async def read_value():
                try:
                    state.convertor = state.convertor(obj)
                except ValueError:
                    # keep wait for normal input
                    return await self.process(on_finish=on_finish)

            if button is not None:
                if button.action == ButtonActions.SKIP:
                    state.convertor = state.convertor(None)
                else:
                    await read_value()
            else:
                await read_value()

            self._dp.message_handlers.unregister(handler)

            try:
                self._next()
            except StopIteration:
                self._sync_cls_states()
                await on_finish(self)
            else:
                await self.process(on_finish=on_finish)

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
