import gex

class Pin(gex.Unit):
    def _type(self):
        return 'PIN'

    def off(self):
        self.send(0x00)

    def on(self):
        self.send(0x01)

    def toggle(self):
        self.send(0x02)
