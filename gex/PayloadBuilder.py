import struct

class PayloadBuilder:
    def __init__(self, endian='little'):
        self.buf = bytearray()
        self.endian = endian

    def close(self):
        return self.buf

    def u8(self, num):
        self.buf.extend(num.to_bytes(length=1, byteorder=self.endian, signed=False))

    def u16(self, num):
        self.buf.extend(num.to_bytes(length=2, byteorder=self.endian, signed=False))

    def u32(self, num):
        self.buf.extend(num.to_bytes(length=4, byteorder=self.endian, signed=False))

    def i8(self, num):
        self.buf.extend(num.to_bytes(length=1, byteorder=self.endian, signed=True))

    def i16(self, num):
        self.buf.extend(num.to_bytes(length=2, byteorder=self.endian, signed=True))

    def i32(self, num):
        self.buf.extend(num.to_bytes(length=4, byteorder=self.endian, signed=True))

    def float(self, num):
        fmt = '<f' if self.endian == 'little' else '>f'
        self.buf.extend(struct.pack(fmt, num))

    def bool(self, num):
        self.buf.append(1 if num != False else 0)

    def str(self, string):
        self.buf.extend(string.encode('utf-8'))
        self.buf.append(0)
