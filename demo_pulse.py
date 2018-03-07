#!/bin/env python3
import gex
import time

with gex.Client(gex.TrxRawUSB()) as client:
    out = gex.DOut(client, 'out')

    out.pulse_us([0], 20)
    out.pulse_us([3], 10)