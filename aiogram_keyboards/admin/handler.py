from ..keyboard import Keyboard
from ..core.button import Button, DialogMeta


class AdminPanel(Keyboard):
    async def __text__(self, meta: DialogMeta):
        return f'Admin panel of {meta.from_user.username}'

    status = Button('Button', 'button')


class Commands(Keyboard):
    __state__ = '*'

    admin = Button('/admin') >> AdminPanel
