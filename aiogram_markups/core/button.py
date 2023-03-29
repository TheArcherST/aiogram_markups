import typing
from typing import Any, Union, Callable, Iterable, Optional, Awaitable
import traceback

from aiogram import Dispatcher
from aiogram.types import InlineKeyboardButton, CallbackQuery, Message
from aiogram.dispatcher.filters.builtin import Filter
from aiogram.dispatcher.filters import Command, StateFilter, Text

from ..configuration import get_dp, logger

from .tools.bind import bind, bind_target_alias
from .tools.handle import handle
from .utils import BoolFilter, hash_text
from .dialog_meta import meta_able_alias, DialogMeta


def group_content_filter(*buttons: 'Button'):
    """Group filter function

    Create telegram filter that union all buttons in list.
    We check **only button content**

    """

    if len(buttons) == 0:
        return BoolFilter(True)

    result = BoolFilter(False)

    for i in buttons:
        result = result.__or__(i.check_content)

    return result


def definition_scope_warn(content: Any, definition_scope: 'DefinitionScope',
                          locate: bool = True, stack_level: int = 3):

    message = f'Content `{content}` conflict at definition scope `{definition_scope!s}`'

    if locate:
        stack = traceback.extract_stack()
        target = stack[-stack_level]
        location = f'{target.filename}:{target.lineno}'
    else:
        location = '<not located>'

    logger.warning(f'{message} at {location}')


class DefinitionScope:
    """Definition Scope object

    Define button scope in bot.

    For example, we have buttons that must
    detects only if state is "test". This
    buttons scope must be...

    >>> scope = DefinitionScope(state='test')

    """

    def __init__(self,
                 commands: Iterable[str] = None,
                 state: str = None,
                 text: Iterable[str] = None,
                 extra_filters: list[Callable] = None,
                 mount_current_build_context: bool = True):

        self.commands = commands
        self.state = state
        self.text = text
        self.extra_filters = extra_filters or []

        self._dp: Optional[Dispatcher] = \
            get_dp() if mount_current_build_context else None

    @property
    def filter(self):
        result = BoolFilter(True)

        def add_condition(*filters: Callable):
            nonlocal result

            for i in filters:
                result = result.__and__(i)

            return None

        if self.commands is not None:
            add_condition(Command(commands=self.commands))
        if self.state is not None:
            add_condition(StateFilter(self.dp, self.state))
        if self.text is not None:
            add_condition(Text(self.text))

        add_condition(*self.extra_filters)

        return result

    def is_conflicts(self, other: 'DefinitionScope') -> bool:
        def eq_or_have_intersection(a: Iterable, b: Iterable):
            if a == b:
                return True
            else:
                intersections = set(a).intersection(b)

                return bool(intersections)

        collisions = [
            self.state == other.state,
            eq_or_have_intersection(self.text, other.text),
            eq_or_have_intersection(self.commands, other.commands)
        ]

        result = all(collisions)

        return result

    async def set_state(self, meta: meta_able_alias):
        meta = DialogMeta(meta)

        dp = get_dp()
        state = dp.current_state(chat=meta.chat_id, user=meta.from_user.id)

        await state.set_state(self.state)

    def mount_dp(self, dp):
        self._dp = dp

    def __str__(self):
        return f'<Scope state="{self.state}">'


class Button:
    """Button object

    Use it to create buttons in TextMarkup
    Include information about button content (text : str)

    >>> button = Button('My button')
    >>> button.text
    'My button'

    """

    CALLBACK_ROOT = '::button::'
    _exemplars: dict[int, list['Button']] = dict()

    def __init__(self,
                 text: Optional[str],
                 data: str = None, *,
                 ignore_state: bool = None,
                 definition_scope: DefinitionScope = None,
                 on_callback: str = None,
                 orientation: int = None,
                 validator: Callable[['DialogMeta'], Awaitable[bool]] = None,
                 is_global: bool = None) -> None:

        """Button initialization method

        You can give as text any obj, it will be replaced on str(obj)

        """

        self.text = text
        self.ignore_state = ignore_state
        self.on_callback = on_callback
        self.data = data
        self.orientation = orientation
        self.validator = validator
        self.is_global = is_global

        self._definition_scope = definition_scope

        self._linked: list[Button] = []

    def __call__(self, *args, **kwargs):
        return self.handle(*args)

    @property
    def definition_scope(self) -> Optional[DefinitionScope]:
        return self._definition_scope

    @definition_scope.setter
    def definition_scope(self, new: Optional[DefinitionScope]) -> None:
        self._definition_scope = new
        self._warn_definition_conflicts(locate_warnings=False)

    def filter(self) -> Filter:
        """Get filter

        Get aiogram filter for telegram objects with
        same content and right definition_scope.

        Support linked buttons.

        :returns Filter object
        """

        definition_scope = self.definition_scope or DefinitionScope(state='*')

        content_filter = group_content_filter(self, *self._linked)
        context_filter = definition_scope.filter

        result = context_filter.__and__(content_filter)

        if self.validator is not None:
            result = result.__and__(self.validator)

        return result

    def check_content(self, obj: Union[Message, CallbackQuery]) -> bool:
        """Check method

        Check if telegram object have same content
        with this button.

        Warning: method ignore linked buttons

        """

        if isinstance(obj, Message):
            result = obj.text == self.text
        elif isinstance(obj, CallbackQuery):
            result = obj.data == self.inline().callback_data
        elif isinstance(obj, DialogMeta):
            result = obj.content == self.text
        else:
            result = False

        return result

    def alias(self, text: Any,
              ignore_state: bool = True,
              on_callback: str = None):

        """Get button alias

        Creates button, linked to self, so, filter
        of this button, include alias filters.

        Note: aliases not linked to self.

        :returns: Button

        """

        if isinstance(text, Button):
            self._linked.extend(text._linked)

        obj = Button(text=text,
                     ignore_state=ignore_state,
                     on_callback=on_callback,
                     definition_scope=self.definition_scope,
                     validator=self.validator)

        self._linked.append(obj)

        return obj

    def __str__(self) -> str:
        return str(self.text)

    def __repr__(self):
        if self.text is None:
            return f'<Abstract Button at {self.definition_scope}>'
        else:
            return f"<Button text='{self.text}' data='{self.data}'>"

    def hex_hash(self):
        if self.definition_scope is not None:
            result = hash_text(str(self.text) + self.definition_scope.state)
        else:
            result = hex(self.__content_hash__())

        return result

    def __hash__(self) -> int:
        return int(self.hex_hash(), base=16)

    def __content_hash__(self) -> int:
        content_hex_hash = hash_text(self.text)
        result = int(content_hex_hash, base=16)

        return result

    def __eq__(self, other) -> bool:
        """ Compare content hash """

        return hash(self) == hash(other)

    def inline(self, data_prefix: str = CALLBACK_ROOT) -> InlineKeyboardButton:
        """Convert to same inline button

        Callback data creating automatically
        It include default prefix and hash of button content

        You can configure data_prefix, but he must end on colon (`:`)
        Do not configure it if you don't know what you do!

        """

        if not data_prefix.endswith(':'):
            raise ValueError(f'Data prefix must ends on colon, '
                             f'but `{data_prefix}` got')

        callback_data = data_prefix + hash_text(self.text)
        result = InlineKeyboardButton(self.text, callback_data=callback_data)

        return result

    def __new__(cls, *args, **kwargs):
        """New method

        Updating _exemplars field

        """

        _exemplar = super().__new__(cls)
        _exemplar.__init__(*args, **kwargs)

        if _exemplar.__content_hash__() in cls._exemplars.keys():
            cls._exemplars[_exemplar.__content_hash__()].append(_exemplar)

            cls._warn_definition_conflicts(_exemplar,
                                           locate_warnings=True)

        else:
            cls._exemplars.update({_exemplar.__content_hash__(): [_exemplar]})

        return _exemplar

    def _warn_definition_conflicts(self, locate_warnings: bool = True) -> bool:
        """Check conflicts method

        Check conflicts with another same content buttons.
        Warns user if need and returns is_conflicts.

        """

        other = self._exemplars[self.__content_hash__()].copy()

        if self.definition_scope is None:
            return False

        if self in other:
            other.remove(self)

        is_conflicts = False

        for i in other:
            if i.definition_scope is None:
                continue

            is_conflicts = self.definition_scope.is_conflicts(i.definition_scope)

            if is_conflicts:
                definition_scope_warn(i.text, i.definition_scope, locate=locate_warnings)
                break

        return is_conflicts

    @classmethod
    def _from_hash(cls, hash_: typing.Union[str, int]) -> list['Button']:
        """Initialization from hash

        Param hash_ is hash in decimal or hex format

        Returns a button, if button with same hash exists
        Else, raise KeyError

        """

        if isinstance(hash_, str):
            hash_ = int(hash_, base=16)

        if hash_ not in cls._exemplars.keys():
            raise KeyError(f'Button with hash `{hash_}` not exists')

        result = cls._exemplars[hash_]

        return result

    @classmethod
    def _from_callback_data(cls, callback_data: str) -> list['Button']:
        """ Initialization from callback data """

        if callback_data.find(':') == -1:
            raise ValueError(f'Callback data must contain colon, '
                             f'but `{callback_data}` got')

        hash_ = callback_data.split(':')[-1]
        result = cls._from_hash(hash_)

        return result

    @classmethod
    def _from_text(cls, text: str) -> list['Button']:
        """Initialization from text

        Returns a button, if button with same text exists
        Else, raise KeyError

        """

        hash_ = int(hash_text(text), base=16)
        result = cls._from_hash(hash_)

        return result

    @classmethod
    async def _search_by_validator(cls, obj: typing.Union[CallbackQuery, Message]):
        for lst in cls._exemplars.values():
            for i in lst:

                if not i.is_global:
                    continue
                if not i.validator:
                    continue

                if await i.validator(DialogMeta(obj)):
                    return i

        return None

    @classmethod
    async def from_telegram_object(cls,
                                   obj: typing.Union[CallbackQuery, Message],
                                   ) -> Optional['Button']:

        """Initialization from telegram object

        Returns a button, if button with same text/call_data exists
        Else, returns None.

        """

        # To find buttons quickly, we not guessing it by all's buttons filters.

        # In first, we choose buttons with same content.

        try:
            if isinstance(obj, CallbackQuery):
                buttons = cls._from_callback_data(obj.data)
            elif isinstance(obj, Message):
                buttons = cls._from_text(obj.text)
            else:
                raise TypeError(f"Can't initialize button from object with type {type(obj)}")
        except (KeyError, ValueError):
            button = await cls._search_by_validator(obj)

            if button is not None:
                buttons = [button]
            else:
                return None

        # Secondly, we search for button with need definition_scope by filter.

        for i in buttons:
            scope_filter = i.definition_scope.filter
            check_result = await scope_filter.check(obj)

            if check_result:
                return i

        else:
            return None

    def handle(self, *filters):
        return handle(self.filter(), *filters)

    def bind(self, target: bind_target_alias):
        return bind(self, target)

    def __rshift__(self, other: bind_target_alias):
        self.bind(other)

        return self

    def __del__(self):
        self._exemplars.pop(self.__content_hash__())

        return None
