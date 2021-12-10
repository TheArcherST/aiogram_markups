from ..action import DialogAction, telegram_object


class ActionSkip(DialogAction):
    async def process(self, obj: telegram_object):
        self.dialog.current.set_result(None)
        await self.dialog.next()


class ActionBack(DialogAction):
    async def process(self, obj: telegram_object):
        await self.dialog.previous(2)
