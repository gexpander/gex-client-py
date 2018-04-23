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

def capture(tr):
    now=datetime.datetime.now()
    now.isoformat()
    data = tr.data
    print("Capture! ")
    print(data)
    np.save("lightning-%s"%now.isoformat(), data)

with gex.Client(gex.TrxRawUSB()) as client:
    adc = gex.ADC(client, 'adc')

    adc.on_trigger(capture)
    adc.setup_trigger(1,
                      level=500,
                      count=1000,
                      edge='rising',
                      pretrigger=250,
                      holdoff=500,
                      auto=True)

    adc.arm()

    sec = 0
    while True:
        print('%d s' % sec)
        sec += 1
        time.sleep(1)
