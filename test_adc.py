#!/bin/env python3
import time

import gex
import numpy as np
from matplotlib import pyplot as plt

from scipy.io import wavfile

with gex.Client(gex.TrxRawUSB()) as client:
    adc = gex.ADC(client, 'adc')

    print(adc.get_calibration_data())
    print(adc.get_channels())

    adc.set_active_channels([1])
    rate=500
    fs = adc.set_sample_rate(rate)

    count = 2000
    data = adc.capture(count)

    print("rx, %d samples" % len(data))
    data = np.add(data / 4096, -0.5)

    #
    if data is not None:
        # wavfile.write('file.wav', rate, data)
        # print("Ok")

        plt.plot(data, 'r.', lw=1)
        plt.show()
    else:
        print("Nothing rx")

