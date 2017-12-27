#!/bin/env python3
import time

import gex
from gex.PayloadParser import PayloadParser
from gex.PayloadBuilder import PayloadBuilder

if False:
    pb = PayloadBuilder()
    pb.u8(128)
    pb.i8(-1)
    pb.u16(1)
    pb.u32(123456789)
    pb.float(3.1415)
    pb.bool(True)
    pb.bool(False)
    pb.str("FUCKLE")

    buf = pb.close()
    print(buf)

    pp = PayloadParser(buf)

    print('>',pp.u8())
    print('>',pp.i8())
    print('>',pp.u16())
    print('>',pp.u32())
    print('>',pp.float())
    print('>',pp.bool())
    print('>',pp.bool())
    print('>',pp.str())

if True:
    client = gex.Gex()

    # Blink a LED at call-sign 1, command 0x02 = toggle
    for i in range(0,10):
        client.send(cs=1, cmd=0x02)
        time.sleep(.1)


#
# port = serial.Serial(
#     port='/dev/ttyACM0',
#     timeout=0.1
# )
#
# print("Send request")
# port.write(b'\x01\x80\x00\x00\x00\x01\x7f')
#
# print("Wait for response")
# rv = port.read(1)
# rv += port.read(port.in_waiting)
#
# print(rv)
