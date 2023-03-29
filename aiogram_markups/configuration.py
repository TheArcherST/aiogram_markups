from typing import Optional

from aiogram import Dispatcher
from loguru import logger


DP: Optional[Dispatcher] = None
_DP_IS_EXPIRED = False

logger = logger


def set_dp(dp: Dispatcher):
    global DP, _DP_IS_EXPIRED

    from aiogram_markups.core.middleware import KeyboardStatesMiddleware

    _DP_IS_EXPIRED = False

    dp.setup_middleware(KeyboardStatesMiddleware(dp))
    DP = dp


def get_dp() -> Dispatcher:
    global DP
    
    if _DP_IS_EXPIRED:
        logger.critical("Aiogram Keyboards tried to access to dispatcher that marked as expired")

        raise RuntimeError("Dispatcher marked as expired")

    if DP is not None:
        return DP
    else:
        logger.critical("Aiogram Keyboards don't installed - Dispatcher not found")

        raise RuntimeError('Dispatcher not found',
                           'Please, call setup method of module `aiogram_markups`, '
                           'method `setup_aiogram_keyboards`')


def mark_dp_expired():
    global _DP_IS_EXPIRED

    _DP_IS_EXPIRED = True
