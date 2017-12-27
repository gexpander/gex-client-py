#!/bin/env python3
import time

import gex

client = gex.Client()
led = gex.Pin(client, 'LED')

for i in range(0,10):
    led.toggle()
    time.sleep(.1)
