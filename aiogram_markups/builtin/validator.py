from typing import Union, Iterable, Protocol

from aiogram.types import Message

from aiogram_markups.validator import Validator
from aiogram_markups.core.dialog_meta import DialogMeta


class IntAble(Protocol):
    def __int__(self): ...


class FloatAble(IntAble, Protocol):
    def __float__(self): ...


class String(Validator):
    def __init__(self, text: Union[str, Iterable[str]] = None):
        if text is None:
            text = set()
        
        if isinstance(text, str):
            text = {text}

        self.text = set(text)

    async def validate(self, meta: 'DialogMeta') -> bool:
        if not self.text:
            if isinstance(meta.source, Message):
                return ((meta.source.content_type == 'text')
                        & (self.null_validate(meta.content)))
            else:
                return self.null_validate(meta.content)

        else:
            return meta.content in self.text

    @staticmethod
    def null_validate(content):
        """ Validate with null setup content """

        return bool(content)


class Integer(String):
    def __init__(self, numbers: Union[IntAble, Iterable[IntAble]] = None):
        if numbers is None:
            numbers = []

        super().__init__(map(str, numbers))

    async def validate(self, meta: 'DialogMeta') -> bool:
        result = await super().validate(meta)
        return result

    @staticmethod
    def null_validate(content):
        return content.isnumeric()


class Float(String):
    def __init__(self, numbers: Union[FloatAble, Iterable[IntAble]] = None):
        if numbers is None:
            numbers = []

        super().__init__(map(str, numbers))

    async def validate(self, meta: 'DialogMeta') -> bool:
        return await super().validate(meta)

    @staticmethod
    def null_validate(content):
        return content.isnumeric()
