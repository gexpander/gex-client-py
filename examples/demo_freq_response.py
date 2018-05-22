#!/bin/env python3
import gex
import numpy as np
from matplotlib import pyplot as plt

# frequency response measurement

with gex.Client(gex.TrxRawUSB()) as client:
    dac = gex.DAC(client, 'dac')
    adc = gex.ADC(client, 'adc')

    dac.waveform(1, 'SINE')
    adc.set_sample_rate(50000)

    table = []

    for i in range(100, 10000, 100):
        dac.set_frequency(1, i)
        data = adc.capture(10000)
        # convert to floats
        samples = data.astype(float)
        amplitude = np.max(samples) - np.min(samples)
        print("%d Hz ... rms %d" % (i, amplitude))
        table.append(i)
        table.append(amplitude)

    dac.dc(1, 0)

    t = np.reshape(np.array(table), [int(len(table)/2),2])
    hz = t[:,0]
    am = t[:,1]

    plt.plot(hz, am, 'r-', lw=1)
    plt.grid()
    plt.show()
