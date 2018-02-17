import time

import gex

with gex.Client(gex.TrxRawUSB()) as client:
    ser = gex.USART(client, 'ser')

    buf = bytearray()
    def decode(data, ts):
        global buf
        buf.extend(data)
        if len(buf) == 9:
            pp = gex.PayloadParser(buf, endian="big")
            pp.skip(2)
            print("%d ppm CO₂" % pp.u16())
            buf = bytearray()
        if len(buf) > 9:
            # something went wrong, clear
            buf = bytearray()


    ser.listen(decode, decode=None)

    while True:
        ser.write([0xFF, 0x01, 0x86, 0, 0, 0, 0, 0, 0x79])
        time.sleep(1)
