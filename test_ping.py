#!/bin/env python3
import time

import gex

with gex.Client(gex.TrxSerialThread(port='/dev/ttyUSB1', baud=57600)) as client:
    pass
    client.close()
