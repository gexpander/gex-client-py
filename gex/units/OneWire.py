import gex

class OneWire(gex.Unit):
    """
    Dallas 1-Wire master
    """

    def _type(self):
        return '1WIRE'

    def test(self):
        return self._query(0x00)
