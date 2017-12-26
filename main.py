#!/bin/env python3
import time

from gex import Gex

gex = Gex()

# Check connection
resp = gex.query_raw(type=Gex.MSG_PING)
print("Ping resp = ", resp.data.decode("ascii"))

# Blink a LED at call-sign 1, command 0x02 = toggle
for i in range(0,10):
    gex.send(cs=1, cmd=0x02)
    time.sleep(.2)


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
