from abc import abstractmethod

from aiogram_keyboards.core.dialog_meta import DialogMeta


class Validator:
    @abstractmethod
    async def validate(self, meta: 'DialogMeta') -> bool:
        pass
