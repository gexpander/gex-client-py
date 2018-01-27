import gex

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

    def arm(self, pins:int, auto:bool=False, confirm:bool=False):
        """
        Arm pins for single shot event generation
        pins - array of pin indices to arm
        auto - use auto trigger (auto re-arm after hold-off)
        """
        pb = gex.PayloadBuilder()
        pb.u16(pins)
        self._send(0x02 if auto else 0x01, pb.close())

    def disarm(self, pins:int, confirm:bool=False):
        """
        DisArm pins
        pins - array of pin indices to arm
        """

        pb = gex.PayloadBuilder()
        pb.u16(pins)
        self._send(0x03, pb.close())

    def on_trigger(self, sensitive_pins, callback):
        """
        Assign a trigger callback.
        Arguments are: pins snapshot, timestamp
        """
        for i in range(0, 16):
            if sensitive_pins & (1 << i):
                self.handlers[i] = callback

    def _on_event(self, event:int, payload, timestamp:int):
        if event == 0x00:
            # trigger interrupt
            pp = gex.PayloadParser(payload)
            triggersource = pp.u16()
            snapshot = pp.u16()

            for i in range(0,16):
                if triggersource & (1<<i):
                    if i in self.handlers:
                        self.handlers[i](snapshot, timestamp)
