#!/bin/env python3
import time

import sys

import gex
import numpy as np
from matplotlib import pyplot as plt
import datetime

from scipy.io import wavfile

data = np.load(sys.argv[1])
plt.plot(data, 'r-', lw=1)
plt.show()
