#!/bin/env python3
import time

import gex
from gex import PayloadParser
from gex import PayloadBuilder

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
    client = gex.Client()
    led = gex.Pin(client, 'LED')

    for i in range(0,10):
        led.toggle()
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
