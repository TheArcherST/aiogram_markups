import abc
from typing import Union, Type, Iterable, Optional, Callable, Awaitable, Literal, TypeVar
from copy import copy


from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, Message, CallbackQuery

from .core.helpers import MarkupType, Orientation
from .core.button import Button
from .core.markup import Markup as MarkupCore, MarkupBehavior
from .core.dialog_meta import DialogMeta
from .core.button import DefinitionScope
from .validator import Validator
from .core.markup_scheme import MarkupScheme, MarkupConstructor


T = TypeVar('T')


class Meta(type, abc.ABC):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)

    def __or__(self: Type['Keyboard'], other: Union[Type['Keyboard'], str]) -> Type['Keyboard']:
        if isinstance(other, self.__class__):
            return self.__or__(other)
        elif isinstance(other, str):
            return self.customize(other)
        else:
            raise ValueError(f"Can't use `{other}` in OR expression with Keyboard")

    def __rshift__(self: Type['Keyboard'], other: Type['Keyboard']):
        self._LINKED.append(other)

    @property
    def chain(self: Type['Keyboard']):
        def method(other: Type['Keyboard']):
            self >> other
            return other
        return method


class Keyboard(metaclass=Meta):
    """Keyboard object

    Due it, you can make more thing, here explained only one.
    You able to make keyboards, that can be processes both in
    the text context and in the callback.

    >>> class MainMenu(Keyboard):
    ...    __text__ = 'Main menu'
    ...
    ...    account = Button('My account')  # row 1
    ...    support = Button('Support')  # row 1
    ...    licence = Button('Licence')  # row 2

    Handle result you can by write handler right in keyboard body.

    >>> class MainMenu(Keyboard):
    ...     ...
    ...
    ...     async def handler(self, meta: DialogMeta):
    ...         message = meta.source
    ...
    ...         await message.answer(f'Your answer: {message.text}')  # equals to meta.content

    To process, just call method `Keyboard.process`.

    Explore all features in documentation.

    """

    async def __text__(self, meta: DialogMeta) -> str:
        """ Method to construct text """

        pass

    async def handler(self, meta: DialogMeta) -> None:
        """ Method what was called on keyboard mention detect """

        pass

    async def validate(self, meta: DialogMeta) -> bool:
        """
        Validate keyboard mention

        Note: Global keyboards mention contains any incoming update.
              Use validator like filter for global keyboards

        """

        pass

    async def markup_construct(self, meta: DialogMeta, constructor: MarkupConstructor) -> Optional[bool]:
        """Runtime markup construct.

        DialogMeta and MarkupScheme here. MarkupScheme is default
        markup of this Keyboard, and you can configure it haw you
        want.

        :returns: markup is exists

        """

        return True

    __text__: Optional[Union[str, Callable[['Keyboard', DialogMeta], Awaitable[Optional[str]]]]]
    __validator__: Validator = None
    __orientation__ = Orientation.UNDEFINED
    __ignore_state__ = False
    __width__ = 1
    __global__ = False
    __definition_scope__: DefinitionScope = None
    __state__ = None  # simple `definition scope` state define
    __markup_scope__ = 'm+c'

    __core__: Optional[MarkupCore] = None

    _ALL_STATES: list[str] = []
    _LINKED: list[Type['Keyboard']] = []
    _CONTEXT = None

    def __class_getitem__(cls, item: Literal[None, False]):
        """
        Method to set __init_subclass__ mode.

        Usage:

        >>> class KeyboardWithLogging(Keyboard[False]):
        ...
        ...     async def handler(self, meta: DialogMeta):
        ...         print(f'Received message from {meta.from_user.first_name}!')


        :case  None: Default mode - full initialization.
        :case False: Just scheme for inherit, no initialization.
                     Use this keyboard ONLY for inherit

        """

        cls._CONTEXT = item

        return cls

    def __init_subclass__(cls, **kwargs):
        cls._LINKED = []

        # marker to initialize null keyboard
        if cls._CONTEXT is False:

            cls._CONTEXT = None
            cls.__base__._CONTEXT = None

            return

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

        # Add zero button to Button engine was able to locate validator
        if len(buttons) == 0:
            buttons.append(Button(None))
            cls.__global__ = True  # if no buttons, keyboard is global

        cls.__core__.buttons = buttons
        cls._synchronize_magic_fields()

        if cls.__validator__ is not None:
            validator = cls.__validator__.validate
        elif cls.validate != Keyboard.validate:
            validator = cls().validate
        else:
            validator = None

        async def handler(meta: DialogMeta):
            await cls().handler(meta)

            for i in cls._LINKED:
                await i.process(meta.source)

        cls.__core__.apply_behavior(MarkupBehavior(handler=handler,
                                                   validator=validator,
                                                   is_global=cls.__global__))

    @classmethod
    def get_choices(cls) -> list[Button]:
        """ Get all buttons """

        return cls.__core__.buttons

    @classmethod
    async def get_markup(cls, meta: DialogMeta) -> ReplyKeyboardMarkup:
        return await cls.__core__.get_markup(meta, MarkupType.TEXT)

    @classmethod
    async def get_inline_markup(cls, meta: DialogMeta) -> InlineKeyboardMarkup:
        return await cls.__core__.get_markup(meta, MarkupType.INLINE)

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

        if isinstance(obj, Button):
            cls.__core__.append(obj)
        elif Keyboard in obj.__bases__:
            cls.__core__.extend(obj.__core__.buttons)
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
    def _unique_context_state(cls) -> str:
        def validate(text: str):
            return text not in cls._ALL_STATES

        result = cls.__name__

        if not validate(result):
            result += '-' + str(cls._ALL_STATES.count(result))

        return result

    @classmethod
    def _configure_state(cls):
        if cls.__state__ is not None:
            state = cls.__state__
        else:
            state = cls._unique_context_state()

        if state is not None:
            cls.__core__.definition_scope = DefinitionScope(state=state)
            cls.__definition_scope__ = cls.__core__.definition_scope

        if cls.__core__.definition_scope.state not in cls._ALL_STATES:
            cls._ALL_STATES.append(cls.__core__.definition_scope.state)

    @classmethod
    def _synchronize_magic_fields(cls):

        cls.__core__.text = cls().__text__
        cls.__core__.width = cls.__width__
        cls.__core__.markup_scope = cls.__markup_scope__
        cls.__core__.definition_scope = cls.__definition_scope__

        cls.__core__.markup_scheme = MarkupScheme(cls().markup_construct)

        if cls.__definition_scope__ is None:
            cls._configure_state()

        cls.__core__.synchronize_buttons(
            orientation=cls.__orientation__,
            definition_scope=cls.__core__.definition_scope,
            ignore_state=cls.__ignore_state__
        )
