#!/bin/env python3
import time

import gex

with gex.Client(gex.TrxRawUSB()) as client:
    print(client.ini_read(1))
