import typing
from typing import Union, Optional
from copy import copy

from aiogram import Bot
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, Message

from .button import Button, group_filter


_alias_black_list = Optional[list[Union[str, Button]]]


class Orientation:
    TOP = -1
    UNDEFINED = 0
    BOTTOM = 1


class KeyboardType:
    INLINE = 'inline'
    TEXT = 'text'


class Meta(type):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)

    def __or__(self, other) -> 'Keyboard':
        return self.__or__(other)


class Keyboard(metaclass=Meta):
    """Text markup states helper

    >>> class MainMenu(Keyboard):
    ...    new_application = Button('🔥 Новая сделка')
    ...    licence = Button('⁉️ Правила')
    ...    support = Button('⚠️Поддержка')


    """

    __text__ = None
    __orientation__ = Orientation.UNDEFINED
    __width__ = 1

    _all: list[Button] = []

    @classmethod
    def get_choices(cls) -> list[Button]:
        """ Get all buttons """

        return cls._all

    def __init_subclass__(cls, **kwargs):
        # select all buttons from cls
        buttons = []

        def recursive_buttons_collect(cls_):
            buttons.extend([value
                            for value in vars(cls_).values()
                            if isinstance(value, Button)])

            if cls_.__base__ != Keyboard:
                return recursive_buttons_collect(cls_.__base__)

        recursive_buttons_collect(cls)

        # assign markup orientation to buttons where it undefined
        for i in buttons:
            if i.orientation is None:
                i.orientation = cls.__orientation__

        cls._all = buttons
        cls._struct_buttons()

    @classmethod
    def _struct_buttons(cls):
        # refresh cls orientation - sub buttons don't inherit it from parents
        cls.__orientation__ = Orientation.UNDEFINED

        # extend `_all` and struct introduction order by buttons orientation
        cls._all = sorted(cls._all,
                          key=lambda button: button.orientation)

    @classmethod
    def get_markup(cls, *,
                   black_list: _alias_black_list = None,
                   one_time_keyboard: bool = True) -> ReplyKeyboardMarkup:

        black_list = black_list or []
        black_list: list[Button] = [Button(i) for i in black_list]

        markup = ReplyKeyboardMarkup(resize_keyboard=True,
                                     row_width=cls.__width__,
                                     one_time_keyboard=one_time_keyboard)

        buttons = [KeyboardButton(button.text)
                   for button in cls.get_choices()
                   if button not in black_list]

        markup.add(*buttons)

        return markup

    @classmethod
    def get_inline_markup(cls, *,
                          black_list: _alias_black_list = None):

        black_list = black_list or []
        black_list: list[Button] = [Button(i) for i in black_list]

        markup = InlineKeyboardMarkup(row_width=cls.__width__)

        buttons = [i.inline()
                   for i in cls.get_choices()
                   if i not in black_list]

        markup.add(*buttons)

        return markup

    @classmethod
    def filter(cls):
        """Filter for KeyBoard

        Creates filter that union all KeyBoard buttons,
        use it to handle data buttons.

        """

        # TODO: replace it on states control
        #
        # This filter able to handle all keyboard
        # buttons and can be used, for example, to
        # handle data buttons. But best is to realize
        # it by states if possible.

        result = group_filter(*cls.get_choices())

        return result

    @classmethod
    def __or__(cls, other: typing.Union['Keyboard', Button]) -> typing.Type['Keyboard']:
        """
        Union method (append), return updated copy
        """

        copy_ = copy(cls)
        copy_.append(other)

        return copy_

    @classmethod
    def extend(cls, objects: typing.Iterable[typing.Union[Button, 'Keyboard']]):
        """
        Extend by buttons or keyboards
        """

        for i in objects:
            cls.append(i)

    @classmethod
    def append(cls, obj: typing.Union[Button, typing.Type['Keyboard']]):
        """
        Append button or all keyboard
        """

        if Button in obj.__bases__:
            cls._all.append(obj)
        elif Keyboard in obj.__bases__:
            cls._all.extend(obj._all)
        else:
            raise NotImplementedError('Method support only `Button` '
                                      'and `Keyboard` types')

        cls._struct_buttons()

    @classmethod
    async def process(cls,
                      bot: Bot,
                      chat_id: int,
                      keyboard_type: str = KeyboardType.TEXT) -> Message:

        if keyboard_type == KeyboardType.TEXT:
            markup = cls.get_markup()
        elif keyboard_type == KeyboardType.INLINE:
            markup = cls.get_inline_markup()
        else:
            raise KeyError(f'Keyboard type `{keyboard_type}` not exists')

        message = await bot.send_message(chat_id, cls.__text__, reply_markup=markup)

        return message

    def __init__(self, text: str):
        self.__text__ = text
