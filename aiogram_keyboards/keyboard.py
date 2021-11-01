from typing import Union, Optional

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup

from .button import Button, group_filter


_alias_black_list = Optional[list[Union[str, Button]]]


class Orientation:
    TOP = -1
    UNDEFINED = 0
    BOTTOM = 1


class Keyboard:
    """Text markup states helper

    >>> class MainMenu(Keyboard):
    ...    new_application = Button('🔥 Новая сделка')
    ...    licence = Button('⁉️ Правила')
    ...    support = Button('⚠️Поддержка')


    """

    __orientation__ = Orientation.UNDEFINED
    __width__ = 1

    _all: list[Button] = []

    @classmethod
    def get_choices(cls) -> list[Button]:
        """ Get all buttons """

        return cls._all

    def __init_subclass__(cls, **kwargs):
        # select all buttons from cls
        buttons = [value
                   for value in vars(cls).values()
                   if isinstance(value, Button)]

        # assign markup orientation to buttons where it undefined
        for i in buttons:
            if i.orientation is None:
                i.orientation = cls.__orientation__

        # refresh cls orientation - sub buttons don't inherit it from parents
        cls.__orientation__ = Orientation.UNDEFINED

        # extend `_all` and struct introduction order by buttons orientation
        cls._all.extend(buttons)
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
