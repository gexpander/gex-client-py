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
        if width==1:
            for i in range(0, count):
                fields.append(pp.u8())
        elif width==2:
            for i in range(0, count):
                fields.append(pp.u16())
        elif width==3:
            for i in range(0, count):
                fields.append(pp.u24())
        elif width==4:
            for i in range(0, count):
                fields.append(pp.u32())
        else:
            raise Exception("Bad width")

        return fields

    def write_reg(self, address:int, reg, value, width:int=1, a10bit:bool=False, endian='little', confirm=True):
        """
        Write a to a single register.
        value can be int or array (in which case `width` applies to each item)
        """
        pb = self._begin_i2c_pld(address, a10bit)
        pb.u8(reg)

        pb.endian = endian
        arr = value
        if type(arr) is int:
            arr = [value]

        if width == 1:
            pb.blob(arr)
        elif width == 2:
            for v in arr:
                pb.u16(v)
        elif width == 3:
            for v in arr:
                pb.u24(v)
        elif width == 4:
            for v in arr:
                pb.u32(v)
        else:
            raise Exception("Bad width")

        self._send(0x02, pb.close(), confirm=confirm)

    def write_byte_data(self, address, reg, value):
        """ Compatibility alias for python3-smbus """
        return self.write_reg(address, reg, value)

    def write_i2c_block_data(self, address, reg, block):
        """ Compatibility alias for python3-smbus """
        return self.write_reg(address, reg, block)
