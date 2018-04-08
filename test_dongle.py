#!/bin/env python3
import time

import gex

with gex.DongleAdapter(gex.TrxRawUSB(remote=True), 0x10) as transport:

    # connect GEX client library to the remote slave
    client = gex.Client(transport)

    adc = gex.ADC(client, "adc")

    print(adc.read_smooth())

    print(adc.read_raw())

    # this will fail unless the communication works
