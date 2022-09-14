from typing import Callable, overload, Literal, Awaitable, Union, Type, Optional

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, InlineKeyboardButton, KeyboardButton, Message
from aiogram.utils.exceptions import MessageCantBeEdited, MessageToEditNotFound

from ..configuration import get_dp, logger

from .button import Button, DefinitionScope
from .helpers import MarkupType, Orientation, MarkupScope
from .dialog_meta import meta_able_alias, DialogMeta
from .utils import BoolFilter, hash_text
from .tools.handle import handle
from .markup_scheme import MarkupScheme, MarkupSchemeButton


class MarkupBehavior:
    def __init__(self,
                 handler: Callable[[DialogMeta], Awaitable[None]] = None,
                 validator: Callable[[DialogMeta], Awaitable[bool]] = None,
                 is_global: bool = False):

        self._handler = handler
        self.validator = validator
        self.is_global = is_global

    @property
    def handler(self):

        async def new(obj):
            button = await Button.from_telegram_object(obj)

            meta = DialogMeta(obj,
                              button=button)

            if self.validator is not None:
                if await self.validator(meta):
                    result = await self._handler(meta)
                else:
                    result = None
            else:
                result = await self._handler(meta)

            return result

        return new


class Markup:
    def __init__(self,
                 buttons: list[Button] = None,
                 text: Union[str, Callable[[DialogMeta], Awaitable[str]]] = None,
                 orientation: str = Orientation.UNDEFINED,
                 ignore_state: bool = False,
                 width: int = 1,
                 one_time_keyboard: bool = True,
                 definition_scope: DefinitionScope = None,
                 markup_scope: str = None,
                 markup_scheme: MarkupScheme = None):

        if buttons is None:
            buttons = []

        self.buttons = buttons
        self.text = text
        self.width = width
        self.one_time_keyboard = one_time_keyboard
        self.markup_scope = markup_scope
        self.markup_scheme = markup_scheme or MarkupScheme()

        self._definition_scope = definition_scope

        self.synchronize_buttons(orientation=orientation,
                                 ignore_state=ignore_state,
                                 definition_scope=self.definition_scope)

    @property
    def rows(self):
        """ Construct raw rows """

        rows = []

        for i in range(len(self.buttons)):
            if i % self.width == 0:
                rows.append([])

            button = self.buttons[i]

            rows[i // self.width].append(MarkupSchemeButton(button=button))

        return rows

    def apply_behavior(self, behavior: MarkupBehavior) -> None:

        # TODO: Refactor.

        if behavior.handler is not None:
            if behavior.is_global:
                content_validator = behavior.validator or BoolFilter(True)
            else:
                content_validator = self.filter(include_scope=False)

            async def new_validator(obj):
                button = await Button.from_telegram_object(obj)
                obj = DialogMeta(obj, button=button)

                result = (bool(await content_validator(obj))
                          & bool(await self.definition_scope.filter(obj)))

                return result

            factory = handle(new_validator)
            factory(behavior.handler)

        self.synchronize_buttons(validator=behavior.validator,
                                 is_global=behavior.is_global)

    def handle(self, func: Callable, *filters) -> None:
        create_handler = handle(self.filter(), *filters)
        create_handler(func)

        return None

    @property
    def definition_scope(self):
        result = self._definition_scope

        if result is None:
            state = self.hex_hash()
            result = DefinitionScope(state=state)

        return result

    @definition_scope.setter
    def definition_scope(self, value: DefinitionScope):
        if value is None:
            return

        self._definition_scope = value

    @overload
    def synchronize_buttons(self, *,
                            soft: bool = True,
                            orientation: str = None,
                            ignore_state: bool = None,
                            definition_scope: DefinitionScope = None,
                            is_global: bool = None,
                            validator: Callable[[DialogMeta], Awaitable[bool]] = None,
                            **kwargs) -> None:

        ...

    def synchronize_buttons(self,
                            soft: bool = True, **kwargs) -> None:

        """Synchronize buttons method

        Provide this params to all buttons in markup.

        Also, here automatically calls buttons struct.

        """

        for i in self.buttons:
            for key, value in kwargs.items():
                actual = getattr(i, key)

                if soft and actual is not None:
                    continue
                else:
                    setattr(i, key, value)

        self.struct_buttons()

        return None

    def struct_buttons(self) -> None:
        """Struct buttons method

        Struct buttons list by `orientation`.

        """

        self.buttons = sorted(self.buttons,
                              key=lambda button: button.orientation or Orientation.UNDEFINED)

        return None

    def sort(self, key: Callable[[Button], bool]):
        """Sort method

        Sort buttons by key.

        Note: Sorting overwrite orientation order!

        """

        # TODO: compare orientation order and sort.
        # Make able to sort only one orientation
        # group, UNDEFINED by default.

        seq = sorted(self.buttons, key=key)
        self.buttons = list(seq)

        return None

    @property
    def is_null(self) -> bool:
        if len(self.buttons) != 1:
            return False

        result = self.buttons[0].text is None

        return result

    @overload
    async def get_markup(self,
                         meta: DialogMeta,
                         markup_type: Literal['TEXT', None]) -> Optional[ReplyKeyboardMarkup]:
        ...

    @overload
    async def get_markup(self,
                         meta: DialogMeta,
                         markup_type: Literal['INLINE']) -> Optional[InlineKeyboardMarkup]:
        ...

    async def get_markup(self,
                         meta: DialogMeta,
                         markup_type: Literal['TEXT', 'INLINE'] = None):

        """Get markup method

        Get TEXT or INLINE markup

        """

        if self.is_null:
            return None

        if markup_type is None:
            markup_type = MarkupType.TEXT

        markup = await self.markup_scheme.get_markup(self.rows, meta, markup_type)

        return markup

    async def process(self,
                      raw_meta: meta_able_alias,
                      markup_scope: Literal['m', 'c', 'm+c'] = None) -> Message:

        """Process method

        Process markup in chat, mentioned in `meta` object.
        Markup scope makes able to hard set keyboard_type.

        :param raw_meta: meta of chat
        :param markup_scope: scope of markup processing
        :returns: Message object

        """

        if self.markup_scope is not None:
            markup_scope = self.markup_scope

        if markup_scope is None:
            markup_scope = 'm+c'

        meta = DialogMeta(raw_meta)
        excepted_markup_type = MarkupScope.cast_to_type(markup_scope, ignore_error=True)

        if meta.markup_type in excepted_markup_type:
            markup_type = meta.markup_type
        else:
            markup_type = excepted_markup_type

        if markup_type == MarkupType.UNDEFINED:
            markup_type = MarkupType.TEXT

        logger.debug(f"Processing `{self.definition_scope.state}` at {meta.chat_id}:{meta.from_user.id}")

        if isinstance(self.text, str):
            text = self.text
        else:
            text = await self.text(meta)

        reply_markup = await self.get_markup(meta, markup_type)

        dp = get_dp()

        if markup_type == MarkupType.TEXT:
            response = await dp.bot.send_message(chat_id=meta.chat_id,
                                                 text=text,
                                                 reply_markup=reply_markup)

        elif markup_type == MarkupType.INLINE:
            try:
                response = await dp.bot.edit_message_text(chat_id=meta.chat_id,
                                                          text=text,
                                                          reply_markup=reply_markup,
                                                          message_id=meta.active_message_id)

            except (MessageCantBeEdited, MessageToEditNotFound):
                response = await dp.bot.send_message(chat_id=meta.chat_id,
                                                     text=text,
                                                     reply_markup=reply_markup)

        else:
            raise KeyError(f"Can't process markup with type {markup_type}")

        # Prepare to markup handle

        await self.definition_scope.set_state(raw_meta)

        return response

    def filter(self, include_scope: bool = True):
        """Filter for KeyBoard

        Creates filter that union all KeyBoard buttons,
        use it to handle data buttons.

        """

        result = BoolFilter(False)

        for i in self.buttons:
            if include_scope:
                result = result.__or__(i.filter())
            else:
                result = result.__or__(i.check_content)

        return result

    def hex_hash(self) -> str:
        summary = ''

        for i in self.buttons:
            summary += str(i.__content_hash__())

        result = hash_text(summary)

        return result

    def __hash__(self) -> int:
        result = int(self.hex_hash(), 16)

        return result

    def append(self, obj: Button):
        self.buttons.append(obj)
        self.synchronize_buttons(definition_scope=self.definition_scope)

    def extend(self, objects: list[Button]):
        self.buttons.extend(objects)
        self.synchronize_buttons(definition_scope=self.definition_scope)
