import gex

class Pin(gex.Unit):
    def __init__(self, client, name):
        super().__init__(client, name, 'PIN')

    def off(self):
        self.send(0x00)

    def on(self):
        self.send(0x01)

    def toggle(self):
        self.send(0x02)
