import gex

class SPI(gex.Unit):
    """
    SPI master direct access
    """

    def _type(self):
        return 'SPI'

    def query(self, slave:int, tbytes, rlen:int, rskip:int=-1, confirm=True):
        """
        Query a slave.

        If rskip is -1 (default), the tbytes length will be used.
        Set it to 0 to skip nothing.

        slave is 0-based index
        """
        if rskip == -1:
            rskip = len(tbytes)

        pb = gex.PayloadBuilder()
        pb.u8(slave)
        pb.u16(rskip)
        pb.u16(rlen)
        pb.blob(tbytes)

        # SPI does not respond if rlen is 0, but can be enforced using 'confirm'
        if rlen > 0:
            resp = self._query(0x00, pb.close())
            return resp.data
        else:
            # write only
            self._send(0x00, pb.close(), confirm=confirm)
            return []

    def write(self, slave:int, tbytes, confirm=True):
        """
        Write with no response received
        """
        self.query(slave, tbytes, rlen=0, rskip=0, confirm=confirm)

    def multicast(self, slaves, tbytes, confirm=True):
        """
        Write with multiple slaves at once.
        Slaves is a right-aligned bitmap (eg. pins 0,2,3 would be 0b1101), or a list of active positions
        """
        pb = gex.PayloadBuilder()
        pb.u16(self.pins2int(slaves))
        pb.blob(tbytes)
        self._send(0x01, pb.close(), confirm=confirm)
