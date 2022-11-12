from typing import Optional

from aiogram import Dispatcher
from loguru import logger


DP: Optional[Dispatcher] = None
logger = logger


def setup_aiogram_keyboards(dp: Dispatcher, terminal_mode: int = 1):
    global DP

    from aiogram_keyboards.core.middleware import KeyboardStatesMiddleware
    from .inspector.app import App

    dp.setup_middleware(KeyboardStatesMiddleware(dp))
    DP = dp

    if terminal_mode == 1:
        logger.info('Aiogram Keyboards greet you!')
    elif terminal_mode == 2:
        logger.remove(0)
        App().run()
    else:
        raise IndexError(f'No Terminal mode {terminal_mode}')


def get_dp() -> Dispatcher:
    global DP

    if DP is not None:
        return DP
    else:
        logger.critical("Aiogram Keyboards don't installed - Dispatcher not found")

        raise RuntimeError('Dispatcher not found',
                           'Please, call setup method of module `aiogram_keyboards`, '
                           'method `setup_aiogram_keyboards`')
