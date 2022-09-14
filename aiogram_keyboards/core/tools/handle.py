from typing import Type, Union, Protocol, Callable

from aiogram.types import ContentTypes

from aiogram_keyboards.configuration import get_dp


class FilterAble(Protocol):
    @classmethod
    def filter(cls, *args, **kwargs):
        pass


handle_target_alias = Union[FilterAble, Type[FilterAble]]


def handle_call(*filters) -> Callable[[Callable], Callable]:
    dp = get_dp()

    def deco(handler):
        dp.register_callback_query_handler(handler, *filters, state='*')

        return handler

    return deco


def handle_message(*filters) -> Callable[[Callable], Callable]:
    dp = get_dp()

    def deco(handler):
        dp.register_message_handler(handler, *filters, state='*', content_types=['any'])

        return handler

    return deco


def handle(*filters) -> Callable[[Callable], Callable]:
    def deco(handler):
        handle_call(*filters)(handler)
        handle_message(*filters)(handler)

        return handler

    return deco
