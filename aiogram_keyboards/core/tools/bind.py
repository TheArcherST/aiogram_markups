from typing import Type, Union, Protocol, TYPE_CHECKING

from aiogram.types import Message, CallbackQuery, ContentTypes
from aiogram.dispatcher.filters import Filter

from aiogram_keyboards.configuration import get_dp

from ..helpers import MarkupType


if TYPE_CHECKING:
    from aiogram_keyboards.keyboard import Keyboard


class FilterAble(Protocol):
    @classmethod
    def filter(cls, *args, **kwargs) -> Filter:
        pass


bind_origin_alias = Union[Type[FilterAble], FilterAble]
bind_target_alias = Union[Type['Keyboard'], 'Keyboard']


def bind_call(origin: bind_origin_alias, target: bind_target_alias) -> None:
    dp = get_dp()

    async def handler(call: CallbackQuery):
        await target.process(call.message, MarkupType.INLINE, active_message=call.message.message_id)

    dp.register_callback_query_handler(handler, origin.filter(), state='*')

    return None


def bind_message(origin: bind_origin_alias, target: bind_target_alias) -> None:
    dp = get_dp()

    async def handler(message: Message):
        await target.process(message, MarkupType.TEXT)

    dp.register_message_handler(handler, origin.filter(), state='*', content_types=['any'])

    return None


def bind(origin: bind_origin_alias, target: bind_target_alias) -> None:
    bind_call(origin, target)
    bind_message(origin, target)

    return None
