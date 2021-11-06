from typing import Optional

from aiogram import Dispatcher

from .middleware import KeyboardStatesMiddleware


DP: Optional[Dispatcher] = None


def setup_aiogram_keyboards(dp: Dispatcher):
    global DP

    dp.setup_middleware(KeyboardStatesMiddleware(dp))
    DP = dp


def get_dp() -> Dispatcher:
    global DP

    if DP is not None:
        return DP
    else:
        raise RuntimeError('Dispatcher not found',
                           'Please, call setup method of module `aiogram_keyboards`, '
                           'method `setup_aiogram_keyboards`')
