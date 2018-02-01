import gex

class OneWire(gex.Unit):
    """
    Dallas 1-Wire master
    """

    def _type(self):
        return '1WIRE'

    def test_presence(self):
        """ Test presence fo any 1wire devices on the bus """
        resp = self._query(0)
        pp = gex.PayloadParser(resp)
        return pp.bool()

    def read_address(self, as_array=False):
        """ Read the address of a lone device on the bus """
        resp = self._query(4)
        pp = gex.PayloadParser(resp)
        if as_array:
            return list(pp.tail())
        else:
            return pp.u64()

    def search(self, alarm=False):
        """ Find all devices, or devices with alarm """
        devices = []

        resp = self._query(2 if alarm else 1)
        hasmore = True
        while hasmore:
            pp = gex.PayloadParser(resp)
            hasmore = pp.bool()
            while pp.length() > 0:
                devices.append(pp.u64())

            if hasmore:
                resp = self._query(3)

        return devices

    def query(self, request, rcount, addr=None, as_array=False):
        """ Query a device """
        pb = gex.PayloadBuilder()
        if addr is not None:
            pb.u64(addr)

        pb.u16(rcount)

        pb.blob(request)

        resp = self._query(11 if addr is None else 13, pb.close())
        return resp.data if not as_array else list(resp.data)

    def write(self, payload, addr=None, confirm=True):
        """ Write to a device """
        pb = gex.PayloadBuilder()
        if addr is not None:
            pb.u64(addr)

        pb.blob(payload)

        self._send(10 if addr is None else 12, pb.close(), confirm=confirm)

    def wait_ready(self):
        """ Wait for DS18x20 to complete measurement (or other chip using the same polling mechanism) """
        self._query(20)