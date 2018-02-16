import gex

class I2C(gex.Unit):
    """
    I2C master direct access
    """

    def _type(self):
        return 'I2C'

    def _begin_i2c_pld(self, address:int, a10bit:bool=False):
        pb = gex.PayloadBuilder()
        if a10bit: address |= 0x8000 # indication for the Unit driver that it's a 10b address
        pb.u16(address)
        return pb

    def write(self, address:int, payload, a10bit:bool=False, confirm=True):
        """
        Write to an address
        """
        pb = self._begin_i2c_pld(address, a10bit)
        pb.blob(payload) # payload to write
        self._send(0x00, pb.close(), confirm=confirm)

    def read(self, address:int, count, a10bit:bool=False):
        """
        Read from an address
        """
        pb = self._begin_i2c_pld(address, a10bit)
        pb.u16(count) # number of bytes to read
        self._query(0x01, pb.close())

    def read_reg(self, address:int, reg, width:int=1, a10bit:bool=False, endian='little'):
        """
        Read a single register
        """
        return self.read_regs(address, reg, count=1, width=width, a10bit=a10bit, endian=endian)[0]

    def read_regs(self, address:int, reg, count:int, width:int=1, a10bit:bool=False, endian='little'):
        """
        Read multiple registers from an address
        """
        pb = self._begin_i2c_pld(address, a10bit)
        pb.u8(reg)
        pb.u16(width*count) # we assume the device will auto-increment (most do)
        resp = self._query(0x03, pb.close())

        fields = []
        pp = gex.PayloadParser(resp.data, endian=endian)
        for i in range(0, count):
            if width==1: fields.append(pp.u8())
            elif width==2: fields.append(pp.u16())
            elif width==3: fields.append(pp.u24())
            elif width==4: fields.append(pp.u32())
            else: raise Exception("Bad width")
        return fields

    def write_reg(self, address:int, reg, value:int, width:int=1, a10bit:bool=False, endian='little', confirm=True):
        """
        Write a to a single register
        """
        pb = self._begin_i2c_pld(address, a10bit)
        pb.u8(reg)

        pb.endian = endian
        if width == 1: pb.u8(value)
        elif width == 2: pb.u16(value)
        elif width == 3: pb.u24(value)
        elif width == 4: pb.u32(value)
        else: raise Exception("Bad width")

        self._send(0x02, pb.close(), confirm=confirm)
