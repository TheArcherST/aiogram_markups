from typing import TypeVar, Optional, Union, Generic, Protocol
from abc import abstractmethod, ABC

from aiogram.types import Message, CallbackQuery


T = TypeVar('T')
TO = TypeVar('TO', CallbackQuery, Message)


class Converter(Protocol[T, TO]):
    """Converter object

    Convert telegram object to need format

    """

    @abstractmethod
    def _convert(self, obj: TO) -> T:
        pass


class ConvertTelegramObj(Converter, Generic[T, TO]):
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
            self.result = self._convert(obj)

    @abstractmethod
    def _convert(self, obj: TO) -> T:
        pass

    def __call__(self: T, obj: Optional[TO]) -> T:
        self.__init__(obj)

        return self


class ConvertCallback(ConvertTelegramObj[T, CallbackQuery]):
    @abstractmethod
    def _convert(self, obj: Optional[CallbackQuery]) -> T:
        pass


class ConvertMessage(ConvertTelegramObj[T, Message]):
    @abstractmethod
    def _convert(self, obj: Optional[Message]) -> T:
        pass
