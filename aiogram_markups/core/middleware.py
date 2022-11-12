"""KeyboardStatesMiddleware

Middleware can detect registered states on pre_process_ and make same actions
For example, if ignore_state on button is True, button text enter will
refresh current state. Same if sent appropriate callback_query.

Also, if button have .data (is not None), message.text or call.data
replacing on it's value. It represented by process_ middlewares.

"""


from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.middlewares import BaseMiddleware

from .button import Button
from .dialog_meta import DialogMeta

from ..configuration import logger


class KeyboardStatesMiddleware(BaseMiddleware):
    def __init__(self, dp: Dispatcher):
        self.dp = dp

        super().__init__()

    async def on_pre_process_message(self, message: Message, *_args):
        if message.text is None:
            return None

        if (button := await Button.from_telegram_object(message)) is None:
            return None
        else:
            meta = DialogMeta(message)
            logger.debug(f'Detected button `{button}` press at {meta.chat_id}:{meta.from_user.id}')

            if button.ignore_state:
                state = self.dp.current_state(chat=message.chat.id, user=message.from_user.id)
                await state.reset_state()

    async def on_pre_process_callback_query(self, call: CallbackQuery, *_args):
        if (button := await Button.from_telegram_object(call)) is None:
            return None
        else:
            meta = DialogMeta(call)
            logger.debug(f'Detected button `{button}` press at {meta.chat_id}:{meta.from_user.id}')

        if button.ignore_state:
            state = self.dp.current_state(chat=call.message.chat.id, user=call.from_user.id)
            await state.reset_state()

        if button.on_callback is not None:
            await call.answer(button.on_callback)

    @staticmethod
    async def on_process_message(message: Message, *_args):
        if message.text is None:
            return None

        if (button := await Button.from_telegram_object(message)) is None:
            return None

        if button.data is not None:
            message.text = button.data

    @staticmethod
    async def on_process_callback_query(call: CallbackQuery, *_args):
        if (button := await Button.from_telegram_object(call)) is None:
            return None

        if button.data is not None:
            call.data = button.data
