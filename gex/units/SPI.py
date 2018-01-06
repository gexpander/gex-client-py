import gex

class SPI(gex.Unit):
    """
    SPI master direct access
    """

    def _type(self):
        return 'SPI'

    def query(self, slave:int, tbytes, rlen:int, rskip:int=-1):
        """
        Query a slave.

        If rskip is -1 (default), the tbytes length will be used.
        Set it to 0 to skip nothing.
        """
        if rskip == -1:
            rskip = len(tbytes)

        pb = gex.PayloadBuilder()
        pb.u8(slave)
        pb.u16(rskip)
        pb.u16(rlen)
        pb.blob(tbytes)
        if rlen > 0:
            resp = self._query(0, pb.close())
            return resp.data
        else:
            # write only
            self._query(0x80, pb.close())
            return []

    def write(self, slave:int, tbytes):
        """
        Write with no response received
        """
        self.query(slave, tbytes, rlen=0, rskip=0)

    def multicast(self, slaves:int, tbytes):
        """
        Write with multiple slaves at once.
        Slaves is a right-aligned bitmap (eg. pins 0,2,3 would be 0b1101)
        """
        pb = gex.PayloadBuilder()
        pb.u16(slaves)
        pb.blob(tbytes)
        # write only
        self._query(0x81, pb.close())
