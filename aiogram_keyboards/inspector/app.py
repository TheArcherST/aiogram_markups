from tabulate import tabulate

from ..core.button import Button, hash_text


class ButtonInspector(Button):
    @classmethod
    def all(cls):
        result = []
        for i in cls._exemplars.values():
            result.extend(i)
        return result

    @classmethod
    def select(cls, content: str):
        return cls._exemplars[int(hash_text(content), base=16)]


class App:
    def __init__(self):
        pass

    def run(self):
        from threading import Thread

        def fun():
            while True:
                request = input('>>> ')

                if request in ('b', 'btn', 'buttons'):
                    lst = []
                    for i in ButtonInspector.all():
                        lst.append((i.text or '<null>', i.definition_scope.state, i.is_global))

                    print(tabulate(lst, headers=['content', 'state', 'is global']))

                print()

        th = Thread(target=fun)
        th.start()
