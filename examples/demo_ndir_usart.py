import time

import gex

# basic NDIR CO2 sensor readout

with gex.Client(gex.TrxRawUSB()) as client:
    ser = gex.USART(client, 'ser')

    while True:
        ser.clear_buffer()
        ser.write([0xFF, 0x01, 0x86, 0, 0, 0, 0, 0, 0x79])
        data = ser.receive(9, decode=None)

        pp = gex.PayloadParser(data, endian="big").skip(2)
        print("%d ppm CO₂" % pp.u16())

        time.sleep(1)
