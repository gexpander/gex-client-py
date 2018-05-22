#!/bin/env python3
import time

import gex
import numpy as np
from matplotlib import pyplot as plt

from scipy.io import wavfile

# catching a transient

with gex.Client(gex.TrxRawUSB()) as client:
    adc = gex.ADC(client, 'adc')

    rate=50000
    fs = adc.set_sample_rate(rate)

    d = None

    def x(report):
        global d
        print("capt")
        d = report

    adc.on_trigger(x)
    adc.setup_trigger(0, 50, 600, edge='rising', pretrigger=100)
    adc.arm()

    time.sleep(2)

    if d is not None:
        plt.plot(d.data, 'r-', lw=1)
        plt.grid()
        plt.show()
    else:
        print("Nothing rx")

