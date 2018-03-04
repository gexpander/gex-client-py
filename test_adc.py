#!/bin/env python3
import time

import gex
import numpy as np
from matplotlib import pyplot as plt

from scipy.io import wavfile

with gex.Client(gex.TrxRawUSB()) as client:
    adc = gex.ADC(client, 'a')

    adc.set_active_channels([3])
    rate=44000
    fs = adc.set_sample_rate(rate)

    count = 44000*2
    data = np.add(adc.capture(count) / 4096, -0.5)

    if data is not None:
        # wavfile.write('file.wav', rate, data)
        # print("Ok")

        plt.plot(data, 'r-', lw=1)
        plt.show()
    else:
        print("Nothing rx")

