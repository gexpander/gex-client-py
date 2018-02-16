import gex
from gex.Client import EventReport


class DIn(gex.Unit):
    """
    Digital input port.
    Pins are represented by bits of a control word, right-aligned.

    For example, if pins C6, C5 and C0 are selected for the unit,
    the read word has the format (bits) |<C6><C5><C0>|
    """

    def _init(self):
        self.handlers = {}

    def _type(self):
        return 'DI'

    def read(self):
        """ Read pins """
        msg = self._query(0x00)
        pp = gex.PayloadParser(msg)
        return pp.u16()

    def arm(self, pins, auto:bool=False, confirm:bool=False):
        """
        Arm pins for single shot event generation
        pins - array of pin indices to arm
        auto - use auto trigger (auto re-arm after hold-off)
        """
        pb = gex.PayloadBuilder()
        pb.u16(self.pins2int(pins))
        self._send(0x02 if auto else 0x01, pb.close())

    def disarm(self, pins, confirm:bool=False):
        """
        DisArm pins
        pins - array of pin indices to arm
        """

        pb = gex.PayloadBuilder()
        pb.u16(self.pins2int(pins))
        self._send(0x03, pb.close())

    def on_trigger(self, sensitive_pins, callback):
        """
        Assign a trigger callback.
        Pins are passed as a list of indices (packed), or a bitmap
        Arguments are: pins snapshot, timestamp
        """

        for i in self.pins2list(sensitive_pins):
            self.handlers[i] = callback

    def _on_event(self, evt:EventReport):
        if evt.code == 0x00:
            # trigger interrupt
            pp = gex.PayloadParser(evt.payload)
            triggersources = pp.u16() # multiple can happen at once
            snapshot = pp.u16()

            for i in range(0,16):
                if triggersources & (1<<i):
                    if i in self.handlers:
                        self.handlers[i](snapshot, evt.timestamp)
