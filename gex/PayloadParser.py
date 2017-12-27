import struct

class PayloadParser:
    def __init__(self, buf, endian='little'):
        self.buf = buf
        self.ptr = 0
        self.endian = endian

    def slice(self, n):
        if self.ptr + n > len(self.buf):
            raise Exception("Out of bounds")

        slice = self.buf[self.ptr:self.ptr + n]
        self.ptr += n
        return slice

    def u8(self):
        slice = self.slice(1)
        return int.from_bytes(slice, byteorder=self.endian, signed=False)

    def u16(self):
        slice = self.slice(2)
        return int.from_bytes(slice, byteorder=self.endian, signed=False)

    def u32(self):
        slice = self.slice(4)
        return int.from_bytes(slice, byteorder=self.endian, signed=False)

    def i8(self):
        slice = self.slice(1)
        return int.from_bytes(slice, byteorder=self.endian, signed=True)

    def i16(self):
        slice = self.slice(2)
        return int.from_bytes(slice, byteorder=self.endian, signed=True)

    def i32(self):
        slice = self.slice(4)
        return int.from_bytes(slice, byteorder=self.endian, signed=True)

    def float(self):
        slice = self.slice(4)
        fmt = '<f' if self.endian == 'little' else '>f'
        return struct.unpack(fmt, slice)[0]

    def bool(self):
        return 0 != self.slice(1)[0]

    def str(self):
        p = self.ptr
        while p < len(self.buf) and self.buf[p] != 0:
            p += 1

        bs = self.slice(p - self.ptr)
        self.ptr += 1
        return bs.decode('utf-8')

    def rewind(self):
        self.ptr = 0

    def tail(self):
        return self.slice(len(self.buf) - self.ptr)
