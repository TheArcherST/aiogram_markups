from ..keyboard import Keyboard
from ..core.button import Button, DefinitionScope, DialogMeta


class AdminPanel(Keyboard):
    @staticmethod
    async def __text__(self, meta: DialogMeta):
        return f'Hello, you chose {meta}'

    status = Button('Status!!')


class Commands(Keyboard):
    __definition_scope__ = DefinitionScope(state='*')

    admin = Button('/admin') >> AdminPanel
