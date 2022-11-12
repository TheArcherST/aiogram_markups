from abc import abstractmethod

from aiogram_markups.core.dialog_meta import DialogMeta


class Validator:
    @abstractmethod
    async def validate(self, meta: 'DialogMeta') -> bool:
        pass
