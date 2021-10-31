import typing
from typing import Any, Union
from warnings import warn

from aiogram.types import InlineKeyboardButton, CallbackQuery, Message
from aiogram.dispatcher.filters.builtin import Filter

from .utils import _hash_text


class FalseFilter(Filter):
    async def check(self, *args) -> bool:
        return False


def group_filter(*buttons: 'Button'):
    """Group filter function

    Create telegram filter that union all buttons in list

    """

    result = FalseFilter()

    for i in buttons:
        result = result.__or__(i.check)

    return result


class Button:
    """Button object

    Use it to create buttons in TextMarkup
    Include information about button content (text : str)

    >>> button = Button('My button')
    >>> button.text
    'My button'

    """

    CALLBACK_ROOT = '::keyboard::'
    _exemplars: dict[int, 'Button'] = dict()

    def __init__(self,
                 text: Any,
                 ignore_state: bool = True,
                 on_callback: str = None,
                 data: str = None) -> None:

        """Button initialization method

        You can give as text any obj, it will be replaced on str(obj)

        """

        text = str(text)

        self.text: str = text
        self.ignore_state = ignore_state
        self.on_callback = on_callback
        self.data = data

        self._linked: list[Button] = []

    def _hex_hash(self):
        return _hash_text(self.text)

    def filter(self) -> Filter:
        """Get filter

        Get aiogram filter for telegram objects with same content
        Supports linked buttons.

        :returns Filter object
        """

        result = group_filter(self, *self._linked)

        return result

    def check(self, obj: Union[Message, CallbackQuery]) -> bool:
        """Check method

        Check if telegram object call for this button
        Supports `Message` and `CallbackQuery` objects

        Warning: method ignore linked buttons

        """

        if isinstance(obj, Message):
            if obj.text == self.text:
                return True

        if isinstance(obj, CallbackQuery):
            if obj.data == self.inline().callback_data:
                return True

        return False

    def alias(self, text: Any,
              ignore_state: bool = True,
              on_callback: str = None):

        """Get button alias

        Creates button, linked to self, so, filter
        of this button, include alias filters.

        :returns: Button

        """

        if isinstance(text, Button):
            self._linked.extend(text._linked)

        obj = Button(text=text,
                     ignore_state=ignore_state,
                     on_callback=on_callback)

        self._linked.append(obj)

        return obj

    def __str__(self) -> str:
        return self.text

    def __repr__(self):
        return (f"<Button text='{self.text}' "
                f"ignore_state={self.ignore_state} "
                f"on_callback={self.on_callback} "
                f"data={self.data}>")

    def __hash__(self) -> int:
        return int(self._hex_hash(), base=16)

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

        callback_data = data_prefix + self._hex_hash()
        result = InlineKeyboardButton(self.text, callback_data=callback_data)

        return result

    def __new__(cls, *args, **kwargs):
        """New method

        Updating _exemplars field

        """

        _ = super().__new__(cls)
        _.__init__(*args, **kwargs)
        exemplar = _

        if exemplar.__hash__() in cls._exemplars.keys():
            equal_exemplar = cls._exemplars[exemplar.__hash__()]

            warn(Warning(
                f'\nCongratulations, you find a MD5 collision! ... or you just repeat button content.\n'
                f'Anyway, button replaced on equals one\n'
            ), stacklevel=2)

            return equal_exemplar

        cls._exemplars.update({exemplar.__hash__(): exemplar})

        return exemplar

    @classmethod
    def _from_hash(cls, hash_: typing.Union[str, int]) -> 'Button':
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
    def _from_callback_data(cls, callback_data: str) -> 'Button':
        """ Initialization from callback data """

        if callback_data.find(':') == -1:
            raise ValueError(f'Callback data must contain colon, '
                             f'but `{callback_data}` got')

        hash_ = callback_data.split(':')[-1]
        result = cls._from_hash(hash_)

        return result

    @classmethod
    def _from_text(cls, text: str):
        """Initialization from text

        Returns a button, if button with same text exists
        Else, raise KeyError

        """

        hash_ = int(_hash_text(text), base=16)
        result = cls._from_hash(hash_)

        return result

    @classmethod
    def from_telegram_object(cls,
                             obj: typing.Union[CallbackQuery, Message]) -> typing.Optional['Button']:

        """Initialization from telegram object

        Returns a button, if button with same text/call_data exists
        Else, returns None

        """

        try:
            if isinstance(obj, CallbackQuery):
                return cls._from_callback_data(obj.data)

            if isinstance(obj, Message):
                return cls._from_text(obj.text)

        except (KeyError, ValueError):
            return None
        else:
            raise NotImplementedError('Method support only  aiogram '
                                      'types `CallbackQuery` and `Message`')
