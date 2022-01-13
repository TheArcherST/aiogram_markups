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
    def _cast(self, obj: Message) -> T:
        photo = obj.photo[0]

        return photo.file_id


class DocumentID(CastMessage[str]):
    def _cast(self, obj: Message) -> T:
        try:
            return obj.document.file_id
        except AttributeError as e:
            raise ValueError(f'Error while cast: {e}')


class Integer(CastTelegramObj[int, TO]):
    def _cast(self, obj: TO) -> T:
        if isinstance(obj, CallbackQuery):
            return int(obj.data)

        if isinstance(obj, Message):
            return int(obj.text)


class Float(CastTelegramObj[float, TO]):
    def _cast(self, obj: TO) -> T:
        if isinstance(obj, CallbackQuery):
            return float(obj.data)

        if isinstance(obj, Message):
            return float(obj.text)


class Text(CastTelegramObj[str, TO]):
    def _cast(self, obj: TO) -> T:
        if isinstance(obj, CallbackQuery):

            if obj.data is None:
                raise ValueError(
                    'Cant convert to text `CallbackQuery` object without `data`.'
                )

            return str(obj.data)

        if isinstance(obj, Message):

            if obj.text is None:
                raise ValueError(
                    'Cant convert to text `Message` object without `text`.'
                )

            return str(obj.text)
