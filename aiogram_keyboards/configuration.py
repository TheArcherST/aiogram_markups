from typing import Optional

from aiogram import Dispatcher
from loguru import logger

from .build_context import BuildContext

context = BuildContext()
DP: Optional[Dispatcher] = None
logger = logger


def setup_aiogram_keyboards(dp: Dispatcher):
    global DP

    from aiogram_keyboards.core.middleware import KeyboardStatesMiddleware

    dp.setup_middleware(KeyboardStatesMiddleware(dp))
    DP = dp

    from .admin import handler

    logger.info('Aiogram Keyboards greet you!')


def get_dp() -> Dispatcher:
    global DP

    if DP is not None:
        return DP
    else:
        logger.critical("Aiogram Keyboards don't installed - Dispatcher not found")

        raise RuntimeError('Dispatcher not found',
                           'Please, call setup method of module `aiogram_keyboards`, '
                           'method `setup_aiogram_keyboards`')
