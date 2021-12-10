from abc import abstractmethod

from .dialog import DialogCore, telegram_object


class DialogAction:
    """Dialog action

    Use object to build button logic
    in your dialog.

    """

    def __init__(self, dialog: 'DialogCore'):
        self.dialog = dialog

    @abstractmethod
    async def process(self, obj: telegram_object) -> None:
        """Process method

        Main method that call while processing
        target button.

        Warning: action `dialog.next()` calls by dialog
        in all cases. For example, to next step was a
        previous, you need move it on -2, so, next step
        was -1 to current. And if you want to repeat
        current step, need to move step on -1.

        """

        pass
