import time

import gex

# sipo example

with gex.Client(gex.TrxRawUSB()) as client:
    sipo = gex.SIPO(client, 'sipo')
    d4 = gex.DOut(client, 'd4')

    # Jort the lights
    sipo.load([
        [0x0a, 0x0f],
        [0xF8, 0xFC],
        [0x00, 0x00],
        [0x02, 0x00],
    ], end=0x04)

    d4.write(1)
    # sipo.set_data(0x04)
    # sipo.store()
