#!/bin/env python3
import time

import gex

with gex.Client(gex.TrxRawUSB()) as client:
    time.sleep(3)
    print("End")

