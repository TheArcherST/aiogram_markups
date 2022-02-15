class BuildContext:
    def __init__(self):
        self.state = None

    def begin(self, state: str):
        self.state = state

    def end(self):
        self.state = None
