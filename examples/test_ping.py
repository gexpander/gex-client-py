#!/bin/env python3
import time

import gex

with gex.Client(gex.TrxSerialThread(port='/dev/ttyACM0')) as client:
    pass
