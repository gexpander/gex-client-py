#!/bin/env python3
import time

import gex

# test with the radio gw

with gex.DongleAdapter(gex.TrxRawUSB(remote=True), 0x10) as transport:
# with gex.TrxRawUSB() as transport:

    # connect GEX client library to the remote slave
    client = gex.Client(transport)

    while True:
        client.query_raw(type=gex.MSG_PING)
        print("ok")
        time.sleep(0.1)

    # do = gex.DOut(client, "led")
    # adc = gex.ADC(client, "adc")
    #
    # while True:
    #     do.toggle(confirm=True)
    #     print(adc.read_smooth())
    #     time.sleep(0.2)

    # adc = gex.ADC(client, "adc")
    # for j in range(10):
    #     try:
    #         print(adc.read_smooth())
    #     except:
    #         print("Failed")
