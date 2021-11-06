"""Built-in converters

- Text
- PhotoID
- DocumentID
- Integer
- Float

"""


from aiogram.types import CallbackQuery, Message

from .convert import ConvertMessage, ConvertTelegramObj, T, TO


class PhotoID(ConvertMessage[str]):
    def _convert(self, obj: Message) -> T:
        photo = obj.photo[0]

        return photo.file_id


class DocumentID(ConvertMessage[str]):
    def _convert(self, obj: Message) -> T:
        return obj.document.file_id


class Integer(ConvertTelegramObj[int, TO]):
    def _convert(self, obj: TO) -> T:
        if isinstance(obj, CallbackQuery):
            return int(obj.data)

        if isinstance(obj, Message):
            return int(obj.text)


class Float(ConvertTelegramObj[float, TO]):
    def _convert(self, obj: TO) -> T:
        if isinstance(obj, CallbackQuery):
            return float(obj.data)

        if isinstance(obj, Message):
            return float(obj.text)


class Text(ConvertTelegramObj[str, TO]):
    def _convert(self, obj: TO) -> T:
        if isinstance(obj, CallbackQuery):
            return str(obj.data)

        if isinstance(obj, Message):
            return str(obj.text)
