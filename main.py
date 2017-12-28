#!/bin/env python3
import time
import gex

client = gex.Client()

if False:
    s = client.ini_read()
    client.ini_write(s)

if False:
    buf = client.bulk_read(gex.MSG_INI_READ)
    print(buf.decode('utf-8'))

    client.bulk_write(gex.MSG_INI_WRITE, buf)

if False:
    led = gex.Pin(client, 'LED')

    for i in range(0,10):
        led.toggle()
        time.sleep(.1)

if True:
    leds = gex.DOut(client, 'TST')

    for i in range(0,0x41):
        leds.write(i&0x3F)
        time.sleep(.1)

if False:
    leds = gex.DOut(client, 'TST')

    for i in range(0, 0x41):
        #leds.write(i & 0x3F)
        leds.toggle(0xFF)
        time.sleep(.1)