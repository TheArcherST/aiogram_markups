from typing import Union, TYPE_CHECKING, Any

from aiogram.types import Message, CallbackQuery, User

from .helpers import MarkupType


if TYPE_CHECKING:
    from .button import Button


class TypeNotExcepted(TypeError):
    def __init__(self, obj):
        if not isinstance(obj, type):
            obj = type(obj)

        msg = f"Can't convert obj with type {obj}, this type not excepted."

        super().__init__(msg)


class Convertor:
    class ConvertAbleAlias:
        chat_id = Union[Message, CallbackQuery, int, str]
        user_id = Union[Message, CallbackQuery, int, str]
        message_id = Union[Message, CallbackQuery, int, str]
        markup_type = Union[Message, CallbackQuery, str]
        data = Any
        state = str
        content = Union[Message, CallbackQuery, str]

        from_user = Union[Message, CallbackQuery]

    @staticmethod
    def chat_id(obj: ConvertAbleAlias.chat_id) -> int:

        if isinstance(obj, Message):
            result = obj.chat.id
        elif isinstance(obj, CallbackQuery):
            result = obj.message.chat.id
        elif isinstance(obj, str):
            result = int(obj)
        elif isinstance(obj, int):
            result = obj
        else:
            raise TypeNotExcepted(obj)

        return result

    @staticmethod
    def message_id(obj: ConvertAbleAlias.message_id) -> int:

        if isinstance(obj, Message):
            result = obj.message_id
        elif isinstance(obj, CallbackQuery):
            result = obj.message.message_id
        elif isinstance(obj, str):
            result = int(obj)
        elif isinstance(obj, int):
            result = obj
        else:
            raise TypeNotExcepted(obj)

        return result

    @staticmethod
    def markup_type(obj: ConvertAbleAlias.markup_type) -> str:
        if isinstance(obj, Message):
            result = MarkupType.TEXT
        elif isinstance(obj, CallbackQuery):
            result = MarkupType.INLINE
        elif isinstance(obj, str):
            result = obj
        else:
            raise TypeNotExcepted(obj)

        return result

    @staticmethod
    def state(obj: ConvertAbleAlias.state) -> str:
        if isinstance(obj, str):
            result = obj
        else:
            raise TypeNotExcepted(obj)

        return result

    @staticmethod
    def data(obj: ConvertAbleAlias.data) -> str:

        if isinstance(obj, Message):
            result = obj.text
        elif isinstance(obj, CallbackQuery):
            result = obj.data
        else:
            result = obj

        return result

    @staticmethod
    def from_user(obj: ConvertAbleAlias.from_user) -> User:
        if isinstance(obj, (Message, CallbackQuery)):
            result = obj.from_user
        else:
            raise TypeNotExcepted(obj)

        return result

    @staticmethod
    def content(obj: ConvertAbleAlias.content) -> str:
        if isinstance(obj, Message):
            result = obj.text
        elif isinstance(obj, CallbackQuery):
            result = obj.data
        elif isinstance(obj, str):
            result = obj
        else:
            raise TypeNotExcepted(obj)

        return result


meta_able_alias = Union[Message, CallbackQuery]


class DialogMeta:
    """Dialog Meta object

    Information about dialog, built by telegram
    object from it and provided state.

    """

    def __init__(self,
                 obj: meta_able_alias,
                 button: 'Button' = None,
                 state: str = '*'):

        if isinstance(obj, DialogMeta):
            self.__dict__ = obj.__dict__
            return

        self.chat_id = Convertor.chat_id(obj)
        self.from_user = Convertor.from_user(obj)
        self.active_message_id = Convertor.message_id(obj)
        self.markup_type = Convertor.markup_type(obj)
        self.data = Convertor.data(obj)
        self.state = Convertor.state(state)

        self.button = button

        if self.button is not None:
            self.content = button.data or button.text
        else:
            self.content = Convertor.content(obj)

        self.source = obj
