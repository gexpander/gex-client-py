#!/bin/env python3
import time

import gex

client = gex.Client()

s = client.ini_read()
client.ini_write(s)

if False:
    buf = client.bulk_read(None, gex.MSG_INI_READ)
    print(buf.decode('utf-8'))

    client.bulk_write(None, gex.MSG_INI_WRITE, buf)

if False:
    led = gex.Pin(client, 'LED')

    for i in range(0,10):
        led.toggle()
        time.sleep(.1)
