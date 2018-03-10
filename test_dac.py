#!/bin/env python3
import time
import math

import gex

from scipy.io import wavfile

with gex.Client(gex.TrxRawUSB()) as client:
    dac = gex.DAC(client, 'dac')

    # dac.set_dither(1, 'TRI', 8)
    # # dac.set_dither(3, 'NONE', 8)
    # # #
    # # # dac.set_frequency(2, 1)
    # # # dac.set_frequency(1, 10.01)
    # dac.set_waveform(1, 'SIN')
    # # dac.set_waveform(2, 'RAMP')
    #
    # dac.rectangle(2, 0.5, 4095, 0)
    #
    # dac.set_frequency(1, 100)
    # dac.set_frequency(2, 50)
    # #
    # dac.sync()

    for i in range(0, 1000):
        dac.set_frequency(1, i)
        time.sleep(0.001)



    # dac.waveform(1, 'SIN')
    # # dac.set_frequency(1, 1000)
    # # dac.dc(1,1000)
    # dac.dc(2,1000)

    #
    # for i in range(0,360*5, 3):
    #     dac.dc_dual(round(2047+math.cos(((i*3.01)/180)*math.pi)*1900),
    #                    round(2047+math.sin(((i*2.01)/180)*math.pi)*1900),
    #                    confirm=False)
    #     time.sleep(0.01)
    #
    # dac.dc_dual(2047,2047)

