import gex

class DIn(gex.Unit):
    """
    Digital input port.
    Pins are represented by bits of a control word, right-aligned.

    For example, if pins C6, C5 and C0 are selected for the unit,
    the read word has the format (bits) |<C6><C5><C0>|
    """

    def _type(self):
        return 'DI'

    def read(self):
        """ Read pins """
        msg = self.query(0x00)
        pp = gex.PayloadParser(msg)
        return pp.u16()
