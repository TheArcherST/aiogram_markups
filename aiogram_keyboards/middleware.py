"""KeyboardStatesMiddleware

Middleware can detect registered states on pre_process_ and make same actions
For example, if ignore_state on button is True, button text enter will
refresh current state. Same if sent appropriate callback_query.

"""


from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.middlewares import BaseMiddleware

from .button import Button


class KeyboardStatesMiddleware(BaseMiddleware):
    def __init__(self, dp: Dispatcher):
        self.dp = dp

        super().__init__()

    async def on_pre_process_message(self, message: Message, *_args):

        if message.text is None:
            return None

        if (button := Button.from_telegram_object(message)) is None:
            return None

        if button.ignore_state:
            state = self.dp.current_state(chat=message.chat.id, user=message.from_user.id)
            await state.reset_state()

    async def on_pre_process_callback_query(self, call: CallbackQuery, *_args):
        if (button := Button.from_telegram_object(call)) is None:
            return None

        if button.ignore_state:
            state = self.dp.current_state(chat=call.message.chat.id, user=call.from_user.id)
            await state.reset_state()

        if button.on_callback is not None:
            await call.answer(button.on_callback)


def setup_keyboard_states(dp: Dispatcher):
    dp.setup_middleware(KeyboardStatesMiddleware(dp))
