#!/bin/env python3
import gex
import time

# this shows a spinny animation on a 30-pixel strip forming a circle

def draw_comet(buf, index):
    r = 0xFF
    g = 0x22
    b = 0x00
    steps = 5
    fades = [0.05, 1, 0.5, 0.1, 0.05]

    for i in range(steps):
        fade = fades[i]
        buf[(len(buf) + index - i)%len(buf)] = \
            round(r * fade)<<16 | \
            round(g * fade)<<8 | \
            round(b * fade)

with gex.Client(gex.TrxRawUSB()) as client:
    # Neopixel strip
    strip = gex.Neopixel(client, 'npx')

    markers = [0, 15]
    for i in range(1000):
        buf = [0]*30
        for j in range(len(markers)):
            n = markers[j]

            draw_comet(buf, n)

            n = n + 1 if n < len(buf)-1 else 0
            markers[j] = n

        strip.load(buf)
        time.sleep(0.02)
        
    strip.clear()
