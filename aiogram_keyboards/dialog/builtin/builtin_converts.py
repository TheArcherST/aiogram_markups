"""Built-in converters

- Text
- PhotoID
- DocumentID
- Integer
- Float

"""


from aiogram.types import CallbackQuery, Message

from ..cast import CastMessage, CastTelegramObj, T, TO


class PhotoID(CastMessage[str]):
    def _convert(self, obj: Message) -> T:
        photo = obj.photo[0]

        return photo.file_id


class DocumentID(CastMessage[str]):
    def _convert(self, obj: Message) -> T:
        return obj.document.file_id


class Integer(CastTelegramObj[int, TO]):
    def _convert(self, obj: TO) -> T:
        if isinstance(obj, CallbackQuery):
            return int(obj.data)

        if isinstance(obj, Message):
            return int(obj.text)


class Float(CastTelegramObj[float, TO]):
    def _convert(self, obj: TO) -> T:
        if isinstance(obj, CallbackQuery):
            return float(obj.data)

        if isinstance(obj, Message):
            return float(obj.text)


class Text(CastTelegramObj[str, TO]):
    def _convert(self, obj: TO) -> T:
        if isinstance(obj, CallbackQuery):
            return str(obj.data)

        if isinstance(obj, Message):
            return str(obj.text)
