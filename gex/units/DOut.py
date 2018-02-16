import gex

class DOut(gex.Unit):
    """
    Digital output port.
    Pins are represented by bits of a control word, right-aligned.

    For example, if pins C6, C5 and C0 are selected for the unit,
    calling the "set" function with a word 0b111 will set all three to 1,
    0b100 will set only C6.
    """

    def _type(self):
        return 'DO'

    def write(self, pins:int, confirm=True):
        """ Set pins to a value - packed, as int """
        pb = gex.PayloadBuilder()
        pb.u16(pins)
        self._send(0x00, pb.close(), confirm=confirm)

    def set(self, pins, confirm=True):
        """ Set pins high - packed, int or list """
        pb = gex.PayloadBuilder()
        pb.u16(self.pins2int(pins))
        self._send(0x01, pb.close(), confirm=confirm)

    def clear(self, pins, confirm=True):
        """ Set pins low - packed, int or list """
        pb = gex.PayloadBuilder()
        pb.u16(self.pins2int(pins))
        self._send(0x02, pb.close(), confirm=confirm)

    def toggle(self, pins, confirm=True):
        """ Toggle pins - packed, int or list """
        pb = gex.PayloadBuilder()
        pb.u16(self.pins2int(pins))
        self._send(0x03, pb.close(), confirm=confirm)
