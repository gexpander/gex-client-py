#!/bin/env python3
import time

import gex
import numpy as np
from matplotlib import pyplot as plt
import datetime

from scipy.io import wavfile

# ADC channel 1 -> 100n -> o -> long wire (antenna)
#                          |
#                          '-> 10k -> GND

led = None

def capture(tr):
    now=datetime.datetime.now()
    now.isoformat()
    data = tr.data
    print("Capture! ")
    print(data)
    np.save("lightning-%s"%now.isoformat(), data)
    led.pulse_ms(250, confirm=False)

with gex.Client(gex.TrxRawUSB()) as client:
    adc = gex.ADC(client, 'adc')
    led = gex.DOut(client, 'led')

    adc.set_sample_rate(60000)

    adc.on_trigger(capture)
    adc.setup_trigger(1,
                      level=2600,
                      count=5000,
                      edge='rising',
                      pretrigger=500,
                      holdoff=500,
                      auto=True)

    adc.arm()

    sec = 0
    while True:
        print('%d s' % sec)
        sec += 1
        time.sleep(1)
