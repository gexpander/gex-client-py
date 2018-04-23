#!/bin/env python3
import time

import gex
import numpy as np
from matplotlib import pyplot as plt

from scipy.io import wavfile

# def show(tr):
#     data = tr.data
#     data = np.add(data / 4096, -0.5)
#     plt.plot(data, 'r-', lw=1)
#     plt.show()

with gex.Client(gex.TrxRawUSB()) as client:
    adc = gex.ADC(client, 'adc')

    adc.on_trigger(lambda tr: print(tr.data))
    adc.setup_trigger(1,
                      level=3500,
                      count=500,
                      edge='rising',
                      pretrigger=100,
                      holdoff=100,
                      auto=True)

    adc.arm()

    while True:
        print('tick')
        time.sleep(1)
