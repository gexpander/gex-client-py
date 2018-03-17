import gex

CMD_WRITE = 0
CMD_SET = 1
CMD_CLEAR = 2
CMD_TOGGLE = 3
CMD_PULSE = 4

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
        self._send(CMD_WRITE, pb.close(), confirm=confirm)

    def set(self, pins, confirm=True):
        """ Set pins high - packed, int or list """
        pb = gex.PayloadBuilder()
        pb.u16(self.pins2int(pins))
        self._send(CMD_SET, pb.close(), confirm=confirm)

    def clear(self, pins, confirm=True):
        """ Set pins low - packed, int or list """
        pb = gex.PayloadBuilder()
        pb.u16(self.pins2int(pins))
        self._send(CMD_CLEAR, pb.close(), confirm=confirm)

    def toggle(self, pins, confirm=True):
        """ Toggle pins - packed, int or list """
        pb = gex.PayloadBuilder()
        pb.u16(self.pins2int(pins))
        self._send(CMD_TOGGLE, pb.close(), confirm=confirm)

    def pulse_ms(self, ms, pins=0b01, active=True, confirm=True):
        """ Send a pulse with length 1-65535 ms on selected pins """
        pb = gex.PayloadBuilder()
        pb.u16(self.pins2int(pins))
        pb.bool(active)
        pb.bool(False)
        pb.u16(ms)
        self._send(CMD_PULSE, pb.close(), confirm=confirm)

    def pulse_us(self, us, pins=1, active=True, confirm=True):
        """ Send a pulse of 1-999 us on selected pins """
        pb = gex.PayloadBuilder()
        pb.u16(self.pins2int(pins))
        pb.bool(active)
        pb.bool(True)
        pb.u16(us)
        self._send(CMD_PULSE, pb.close(), confirm=confirm)





