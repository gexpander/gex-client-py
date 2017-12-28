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

    def write(self, pins:int):
        """ Set pins to a value """
        pb = gex.PayloadBuilder()
        pb.u16(pins)
        self.send(0x00, pb.close())

    def set(self, pins:int):
        """ Set pins high """
        pb = gex.PayloadBuilder()
        pb.u16(pins)
        self.send(0x01, pb.close())

    def clear(self, pins:int):
        """ Set pins low """
        pb = gex.PayloadBuilder()
        pb.u16(pins)
        self.send(0x02, pb.close())

    def toggle(self, pins:int):
        """ Toggle pins """
        pb = gex.PayloadBuilder()
        pb.u16(pins)
        self.send(0x03, pb.close())
