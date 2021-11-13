import abc
from typing import Type, Union, Protocol, Callable

from ..configuration import get_dp


class FilterAble(Protocol):
    @classmethod
    def filter(cls, *args, **kwargs):
        pass


handle_target_alias = Union[FilterAble, Type[FilterAble]]


def handle_call(target: handle_target_alias, *filters) -> Callable[[Callable], Callable]:
    dp = get_dp()

    def deco(handler):
        dp.register_callback_query_handler(handler, target.filter(), *filters)

        return handler

    return deco


def handle_message(target: handle_target_alias, *filters) -> Callable[[Callable], Callable]:
    dp = get_dp()

    def deco(handler):
        dp.register_message_handler(handler, target.filter(), *filters)

        return handler

    return deco


def handle(target: handle_target_alias, *filters) -> Callable[[Callable], Callable]:
    def deco(handler):
        handle_call(target, *filters)(handler)
        handle_message(target, *filters)(handler)

        return handler

    return deco
