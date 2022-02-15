from typing import Type, Optional, TYPE_CHECKING

from aiogram_keyboards.keyboard import Keyboard
from ..dialog.cast import CastTelegramObj
from aiogram_keyboards.core.utils import _hash_text
from ..configuration import logger


if TYPE_CHECKING:
    from .dialog import DialogCore, telegram_object


class State:
    def __init__(self,
                 name: str,
                 convertor: Type[CastTelegramObj],
                 keyboard: Optional[Type[Keyboard]],
                 dialog: 'DialogCore' = None):

        self.name = name
        self.keyboard = keyboard
        self._dialog = dialog

        self.convertor: Type[CastTelegramObj] = convertor
        self._result: Optional[CastTelegramObj] = None

    @property
    def dialog(self) -> 'DialogCore':
        if self._dialog is None:
            raise RuntimeError(f'State {self} not connected to dialog, connect it by method `connect_dialog`')

        return self._dialog

    def connect_dialog(self, dialog: 'DialogCore') -> None:
        self._dialog = dialog

    def set_result(self, obj: Optional['telegram_object']) -> None:

        try:
            self._result = self.convertor(obj)
        except Exception:
            logger.debug(f'{self}: error while cast result')
            raise
        else:
            logger.debug(f'{self}: result is set')

        return None

    @property
    def result(self) -> 'CastTelegramObj':
        if self._result is None:
            raise RuntimeError('Cant fetch state result, telegram objects steel not provided')

        return self._result

    def __repr__(self):
        if self.is_finished:
            status = 'Finished'
        else:
            status = 'Processing'

        if self._dialog is not None:
            chat_postfix = f' at {self._dialog.chat_id}'
        else:
            chat_postfix = ''

        return f'<{status} state "{self.name}"' + chat_postfix + '>'

    @property
    def is_finished(self) -> bool:
        return self._result is not None

    def hex_hash(self):
        """
        Get dialog current state hash
        """

        dialog_hash = self.dialog.hex_hash()
        result = dialog_hash + _hash_text(f'::state-{self.name}::')

        return _hash_text(result)

    async def set(self):
        """
        Set this state to dispatcher
        """

        current_state = self.dialog.dp.current_state(chat=self.dialog.chat_id,
                                                     user=self.dialog.chat_id)
        await current_state.set_state(self.hex_hash())
