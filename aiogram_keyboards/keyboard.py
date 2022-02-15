import abc
from typing import Union, Type, Iterable, Optional, Callable, Awaitable, overload
from copy import copy

from aiogram.types import ReplyKeyboardMarkup, Message, CallbackQuery

from .core.helpers import MarkupType, Orientation
from .core.button import Button
from .core.markup import Markup as MarkupCore, MarkupBehavior
from .core.dialog_meta import DialogMeta


class Meta(type):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)

    def __or__(self: Type['Keyboard'], other: Union[Type['Keyboard'], str]) -> Type['Keyboard']:
        if isinstance(other, self.__class__):
            return self.__or__(other)
        elif isinstance(other, str):
            return self.customize(other)
        else:
            raise ValueError(f"Can't use `{other}` in OR expression with Keyboard")


class Keyboard(metaclass=Meta):
    """Text markup states helper

    >>> class MainMenu(Keyboard):
    ...    new_application = Button('🔥 Новая сделка')
    ...    licence = Button('⁉️ Правила')
    ...    support = Button('⚠️Поддержка')


    """

    __text__: Optional[Union[str, Callable[['Keyboard', DialogMeta], Awaitable[Optional[str]]]]]

    async def __text__(self, meta: DialogMeta) -> Optional[str]:
        return None

    __orientation__ = Orientation.UNDEFINED
    __ignore_state__ = False
    __definition_scope__ = None
    __width__ = 1
    __buttons__ = []

    __core__: Optional[MarkupCore] = None

    def __init__(self, meta: DialogMeta):
        self.meta = meta

    async def handler(self) -> None:
        pass

    @classmethod
    def get_choices(cls) -> list[Button]:
        """ Get all buttons """

        return cls.__core__.buttons

    def __init_subclass__(cls, **kwargs):
        cls.__core__ = MarkupCore()

        # select all buttons from cls
        buttons: list[Button] = []

        def recursive_buttons_collect(cls_):
            buttons.extend([value
                            for value in vars(cls_).values()
                            if isinstance(value, Button)])

            if cls_.__base__ != Keyboard:
                return recursive_buttons_collect(cls_.__base__)

        recursive_buttons_collect(cls)

        cls.__core__.buttons = buttons
        cls._synchronize_magic_fields()

        cls.__core__.apply_behavior(MarkupBehavior(handler=cls.handler))

    @classmethod
    def get_markup(cls) -> ReplyKeyboardMarkup:
        return cls.__core__.get_markup(MarkupType.TEXT)

    @classmethod
    def get_inline_markup(cls):
        return cls.__core__.get_markup(MarkupType.INLINE)

    @classmethod
    def filter(cls):
        return cls.__core__.filter()

    @classmethod
    def __or__(cls, other: Union['Keyboard', Button]) -> Type['Keyboard']:
        """
        Union method (append), return updated copy
        Also inherit `__text__` field
        """

        copy_ = cls.copy()
        copy_.append(other)

        if copy_.__text__ is None:
            copy_.__text__ = other.__text__

        return copy_

    @classmethod
    def extend(cls, objects: Iterable[Union[Button, 'Keyboard']]):
        """
        Extend by buttons or keyboards
        """

        for i in objects:
            cls.append(i)

    @classmethod
    def append(cls, obj: Union[Button, Type['Keyboard']]):
        """
        Append button or all keyboard
        """

        if Button in obj.__bases__:
            cls.__core__.buttons.append(obj)
        elif Keyboard in obj.__bases__:
            cls.__core__.buttons.extend(obj.__core__.buttons)
        else:
            raise NotImplementedError('Method support only `Button` '
                                      'and `Keyboard` types')

        cls.__core__.struct_buttons()

    @classmethod
    async def process(cls,
                      obj: Union[Message, CallbackQuery],
                      markup_type: str = None) -> Message:

        """Process keyboard method

        Processing keyboard in passed chat

        """

        cls._synchronize_magic_fields()

        result = await cls.__core__.process(obj, markup_type)

        return result

    @classmethod
    def customize(cls, text: str) -> Type['Keyboard']:
        new = cls.copy()
        new.__core__.text = text

        return new

    @classmethod
    def copy(cls) -> Type['Keyboard']:
        new_core = copy(cls.__core__)
        new = copy(cls)
        new.__core__ = new_core

        return new

    @classmethod
    def _synchronize_magic_fields(cls):

        cls.__core__.text = cls.__text__
        cls.__core__.width = cls.__width__
        cls.__core__.definition_scope = cls.__definition_scope__

        cls.__core__.synchronize_buttons(
            orientation=cls.__orientation__,
            definition_scope=cls.__core__.definition_scope,
            ignore_state=cls.__ignore_state__
        )
