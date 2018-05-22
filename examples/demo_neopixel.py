#!/bin/env python3
import gex

# the most basic neopixel demo

with gex.Client(gex.TrxRawUSB()) as client:
    # Neopixel strip
    strip = gex.Neopixel(client, 'npx')
    # Load RGB to the strip
    strip.load([0xFF0000, 0x00FF00, 0x0000FF, 0xFF00FF])

