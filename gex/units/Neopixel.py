import gex

class Neopixel(gex.Unit):
    """
    Raw access to a neopixel strip.
    """

    def _type(self):
        return 'NPX'

    def get_len(self):
        """ Get the neopixel strip length """
        resp = self._query(0x04)
        pp = gex.PayloadParser(resp)
        return pp.u16()

    def load(self, colors, reverse=True, confirm=True):
        """
        Load colors to the strip.

        The numbers are normally 0xRRGGBB
        If 'reverse' is false, they're treated as little-endian: 0xBBGGRR.
        """
        pb = gex.PayloadBuilder(endian='big' if reverse else 'little')
        for c in colors:
            pb.u24(c)
        self._send(0x01, pb.close(), confirm=confirm)

    def clear(self, confirm=True):
        """
        Reset the strip (set all to black)
        """
        self._send(0x00, confirm=confirm)
