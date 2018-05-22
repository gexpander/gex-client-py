#!/bin/env python3
import time

import gex

# with gex.Client(gex.TrxRawUSB()) as client:
with gex.DongleAdapter(gex.TrxRawUSB(remote=True), 0x10) as transport:
    client = gex.Client(transport)
    print(client.ini_read(0))
