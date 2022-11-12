from typing import TypeVar, Optional, Generic, Protocol
from abc import abstractmethod

from aiogram.types import Message, CallbackQuery


T = TypeVar('T')
TO = TypeVar('TO', CallbackQuery, Message)


class CastTelegramObjProto(Protocol[T, TO]):
    """Converter object

    Convert telegram object to need format

    """

    @abstractmethod
    def _cast(self, obj: TO) -> T:
        pass


class CastTelegramObj(CastTelegramObjProto, Generic[T, TO]):
    """Converter object

    Convert telegram object to need format
    This class help to implement convert logic
    and connect it to dialog.

    """
    def __init__(self, obj: Optional[TO]):
        self.obj = obj

        if obj is None:
            self.result = None
        else:
            self.result = self._cast(obj)

    @abstractmethod
    def _cast(self, obj: TO) -> T:
        pass

    def __call__(self: T, obj: Optional[TO]) -> T:
        self.__init__(obj)

        return self


class CastCallback(CastTelegramObj[T, CallbackQuery]):
    @abstractmethod
    def _cast(self, obj: Optional[CallbackQuery]) -> T:
        pass


class CastMessage(CastTelegramObj[T, Message]):
    @abstractmethod
    def _cast(self, obj: Optional[Message]) -> T:
        pass
