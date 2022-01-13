from typing import Union, Optional, Type, Any, Iterable
from abc import abstractmethod
from copy import copy

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, Message, CallbackQuery

from .button import Button, group_filter
from .configuration import get_dp
from .helpers import KeyboardType, Orientation
from .utils import get_chat_id, contain_chat_id_alias

from .tools.bind import bind, bind_target_alias
from .tools.handle import handle


_alias_black_list = Optional[list[Union[str, Button]]]


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

    __text__ = None
    __orientation__ = Orientation.UNDEFINED
    __ignore_state__ = True
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
            if i.ignore_state is None:
                i.ignore_state = cls.__ignore_state__

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
    def __or__(cls, other: Union['Keyboard', Button]) -> Type['Keyboard']:
        """
        Union method (append), return updated copy
        Also inherit `__text__` field
        """

        copy_ = copy(cls)
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
            cls._all.append(obj)
        elif Keyboard in obj.__bases__:
            cls._all.extend(obj._all)
        else:
            raise NotImplementedError('Method support only `Button` '
                                      'and `Keyboard` types')

        cls._struct_buttons()

    @classmethod
    async def process(cls,
                      obj: contain_chat_id_alias,
                      keyboard_type: str = None,
                      active_message: int = None) -> Message:

        """Process keyboard method

        Processing keyboard in passed chat

        """

        if cls.__text__ is None:
            raise RuntimeError(f"Can't process keyboard {cls}, `__text__` field is empty")

        bot = get_dp().bot

        def infer_keyboard_type(passed_object: Any, default: str = KeyboardType.TEXT):
            if isinstance(passed_object, Message):
                return KeyboardType.TEXT
            if isinstance(passed_object, CallbackQuery):
                return KeyboardType.INLINE

            return default

        chat_id = get_chat_id(obj)
        keyboard_type = keyboard_type or infer_keyboard_type(obj)

        if keyboard_type == KeyboardType.TEXT:
            markup = cls.get_markup()
        elif keyboard_type == KeyboardType.INLINE:
            markup = cls.get_inline_markup()
        else:
            raise KeyError(f'Keyboard type `{keyboard_type}` not exists')

        if active_message is None:
            message = await bot.send_message(chat_id, cls.__text__, reply_markup=markup)
        else:
            message = await bot.edit_message_text(cls.__text__, chat_id, active_message, reply_markup=markup)

        return message

    @classmethod
    def handle(cls, *filters):
        return handle(cls, *filters)

    @classmethod
    def bind(cls, target: bind_target_alias):
        return bind(cls, target)

    @classmethod
    def __rshift__(cls, other: bind_target_alias) -> Type['Keyboard']:
        cls.bind(other)

        return cls

    @classmethod
    def customize(cls, text: str) -> Type['Keyboard']:
        class CustomKeyboard(cls):
            __text__ = text

        return CustomKeyboard


class AbstractKeyboard(Keyboard):
    def __init__(self, **kwargs):
        """AbstractKeyboard initialization method

        Here you must request need arguments to make keyboard
        and to all buttons what you want change, and pass to
        this method kwargs: keys is button names, values is new
        button text. You can not overwrite method if you not see
        hints or pass args without keywords.

        """

        for key, value in kwargs.items():

            ignore_state = None
            on_callback = None

            if isinstance(value, str):
                text = value
            elif isinstance(value, Button):
                text = value.text
                ignore_state = value.ignore_state
                on_callback = value.on_callback
            else:
                raise TypeError("")

            self.change_button(getattr(self, key),
                               new_text=text,
                               ignore_state=ignore_state,
                               on_callback=on_callback)

    def change_button(self,
                      button: Button,
                      new_text: str,
                      ignore_state: bool = None,
                      on_callback: str = None):

        """ Change button in keyboard """

        self._all.remove(button)

        button = button.alias(text=new_text,
                              ignore_state=ignore_state,
                              on_callback=on_callback)

        self._all.append(button)

        return None
