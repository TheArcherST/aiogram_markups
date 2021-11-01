from typing import Union, Optional

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup

from .button import Button, group_filter


_alias_black_list = Optional[list[Union[str, Button]]]


class Keyboard:
    """Text markup states helper

    >>> class MainMenu(Keyboard):
    ...    new_application = Button('🔥 Новая сделка')
    ...    licence = Button('⁉️ Правила')
    ...    support = Button('⚠️Поддержка')


    """

    # TODO: make it safe to inherit.
    #
    # Now, we cat set parent class buttons
    # in end of the markup. Need create
    # params, providing an opportunity
    # to pin button in need place on the
    # markup, saved while inhering.

    _all: list[Button] = None
    _row_width = 1

    @classmethod
    def get_choices(cls) -> list[Button]:
        """ Get all buttons """

        if cls._all is None:
            cls._repair_all()

        return cls._all

    @classmethod
    def _repair_all(cls):
        """ Repair field `_all` """

        if cls._all is None:
            cls._all = []
            for i in (cls, *cls.__subclasses__()):
                cls._all.extend([value
                                for value in vars(i).values()
                                if isinstance(value, Button)])

    @classmethod
    def get_markup(cls, *,
                   black_list: _alias_black_list = None,
                   one_time_keyboard: bool = True) -> ReplyKeyboardMarkup:

        black_list = black_list or []
        black_list: list[Button] = [Button(i) for i in black_list]

        markup = ReplyKeyboardMarkup(resize_keyboard=True,
                                     row_width=cls._row_width,
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

        markup = InlineKeyboardMarkup(row_width=cls._row_width)

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
