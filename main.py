#!/bin/env python3
import time

import gex

client = gex.Client()

buf = client.bulk_read(None, gex.MSG_INI_READ)
print(buf.decode('utf-8'))

if False:
    led = gex.Pin(client, 'LED')

    for i in range(0,10):
        led.toggle()
        time.sleep(.1)
