import pytest

from aiogram.types import Message
from aiogram_keyboards.core.button import DefinitionScope


@pytest.mark.asyncio
async def test_commands():
    scope = DefinitionScope(commands=['start', 'ex'])

    assert await scope.filter(Message(text='/start'))
    assert await scope.filter(Message(text='/ex'))
    assert not await scope.filter(Message(text='/noway'))
    assert not await scope.filter(Message(text='not command.'))


@pytest.mark.asyncio
async def test_text():
    scope = DefinitionScope(text=['start', 'other text.'])

    assert not await scope.filter(Message(text='other text./'))
    assert not await scope.filter(Message(text='other'))
    assert await scope.filter(Message(text='other text.'))
    assert await scope.filter(Message(text='start'))
