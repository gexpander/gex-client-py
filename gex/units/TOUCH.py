import gex
from gex.Client import EventReport

CMD_READ = 0
CMD_SET_BIN_THR = 1
CMD_DISABLE_ALL_REPORTS = 2
CMD_GET_CH_COUNT = 10

class TOUCH(gex.Unit):
    """
    Touch sensing
    """

    def _init(self):
        self._handlers = {}

    def _type(self):
        return 'TOUCH'

    def read(self):
        """ Read raw values """

        msg = self._query(CMD_READ)
        pp = gex.PayloadParser(msg)

        items = []
        while pp.length() > 0:
            items.append(pp.u16())

        return items

    def set_button_thresholds(self, thresholds, confirm=True):
        """ Set binary report thresholds """
        pb = gex.PayloadBuilder()
        for t in thresholds:
            pb.u16(t)

        self._send(CMD_SET_BIN_THR, pb.close(), confirm=confirm)

    def disable_button_mode(self, confirm=True):
        """ Disable all button reports by clearing the thresholds """
        self._send(CMD_DISABLE_ALL_REPORTS, confirm=confirm)

    def get_channel_count(self, confirm=True):
        """ Read nbr of channels """
        resp = self._query(CMD_GET_CH_COUNT)
        pp = gex.PayloadParser(resp)
        return pp.u8()

    def listen(self, nb, handler):
        self._handlers[nb] = handler

    def _on_event(self, evt:EventReport):
        l = []
        pp = gex.PayloadParser(evt.payload)
        snap = pp.u32()
        changed = pp.u32()

        for i in range(0, 32):
            if changed & (1 << i):
                if i in self._handlers:
                    self._handlers[i]((snap & (1 << i)) != 0, evt.timestamp)


