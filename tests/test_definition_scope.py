import pytest

from aiogram import Dispatcher, Bot
from aiogram.types import Message
from aiogram_markups import setup_aiogram_keyboards
from aiogram_markups.core.button import DefinitionScope


@pytest.fixture()
def dp():
    bot = Bot('1:faketoken')
    dispatcher = Dispatcher(bot)

    setup_aiogram_keyboards(dispatcher)


@pytest.mark.asyncio
async def test_commands(dp):
    scope = DefinitionScope(commands=['start', 'ex'])

    assert await scope.filter(Message(text='/start'))
    assert await scope.filter(Message(text='/ex'))
    assert not await scope.filter(Message(text='/noway'))
    assert not await scope.filter(Message(text='not command.'))


@pytest.mark.asyncio
async def test_text(dp):
    scope = DefinitionScope(text=['start', 'other text.'])

    assert not await scope.filter(Message(text='other text./'))
    assert not await scope.filter(Message(text='other'))
    assert await scope.filter(Message(text='other text.'))
    assert await scope.filter(Message(text='start'))
