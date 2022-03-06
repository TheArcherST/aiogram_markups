from typing import overload, Callable, Awaitable, Optional, Union

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from .dialog_meta import DialogMeta
from .button import Button
from .helpers import MarkupType


class MarkupSchemeButton:
    @overload
    def __init__(self,
                 text: str,
                 data: str = None,
                 url: str = None,
                 row_width: int = 1):

        pass

    @overload
    def __init__(self, *,
                 button: Button,
                 row_width: int = 1):
        pass

    def __init__(self,
                 text: str = None,
                 callback_data: str = None,
                 url: str = None,
                 button: Button = None,
                 row_width: int = 1):

        if button is not None:
            text = button.text
            callback_data = button.inline().callback_data

        self.text = text
        self.callback_data = callback_data
        self.url = url
        self.row_width = row_width


class MarkupConstructor:
    """ Object, that helps you fastly change markup """

    def __init__(self, rows: list[list[MarkupSchemeButton]]):
        self.rows = rows

    @property
    def buttons(self):
        for i in self.rows:
            yield from i

    def add(self,
            row: int,
            button: MarkupSchemeButton):

        self.rows[row].append(button)

    def remove(self,
               row: int,
               col: int):

        self.rows[row].pop(col)


class MarkupScheme:
    def __init__(self,
                 construct: Callable[[DialogMeta, MarkupConstructor],
                                     Awaitable[Optional[bool]]] = None):

        self.construct = construct

    async def apply_construct(self,
                              meta: DialogMeta,
                              rows: list[list[MarkupSchemeButton]]
                              ) -> Optional[list[list[MarkupSchemeButton]]]:

        if self.construct is not None:
            constructor = MarkupConstructor(rows.copy())
            is_actual = await self.construct(meta, constructor)

            if is_actual is False:
                return None
            else:
                rows = constructor.rows

        return rows

    async def get_markup(self,
                         rows: list[list[MarkupSchemeButton]],
                         meta: DialogMeta,
                         markup_type: str) -> Optional[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]]:

        rows = await self.apply_construct(meta, rows)

        if rows is None:
            return None

        if markup_type == MarkupType.TEXT:
            markup = ReplyKeyboardMarkup()
        elif markup_type == MarkupType.INLINE:
            markup = InlineKeyboardMarkup()
        else:
            raise KeyError(f'No markup type {markup_type}')

        for i in rows:
            if markup_type == MarkupType.TEXT:
                markup.row(*[KeyboardButton(j.text)
                             for j in i])

            elif markup_type == MarkupType.INLINE:
                markup.row(*[InlineKeyboardButton(j.text,
                                                  callback_data=j.callback_data,
                                                  url=j.url)

                             for j in i])
            else:
                raise RuntimeError()

        return markup
