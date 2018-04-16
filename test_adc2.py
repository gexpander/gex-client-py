#!/bin/env python3
import time

import gex
import numpy as np
from matplotlib import pyplot as plt

from scipy.io import wavfile

with gex.Client(gex.TrxRawUSB()) as client:
    adc = gex.ADC(client, 'adc')

    for i in range(1000):
        print(adc.read_raw())

