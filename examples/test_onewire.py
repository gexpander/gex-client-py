#!/bin/env python3
import time

import gex

with gex.Client(gex.TrxRawUSB()) as client:
    ow = gex.OneWire(client, 'ow')
    # print("Presence: ", ow.test_presence())
    print("Devices:", ow.search())

    def meas(addr):
        ow.write([0x44], addr=addr)
        ow.wait_ready()
        data = ow.query([0xBE], 9, addr=addr)
        pp = gex.PayloadParser(data)
        return pp.i16() * 0.0625

    def meas2(addr, addr2):
        ow.write([0x44], addr=addr)
        ow.write([0x44], addr=addr2)
        ow.wait_ready()

        data = ow.query([0xBE], 9, addr=addr)
        pp = gex.PayloadParser(data)
        a = pp.i16() * 0.0625

        data = ow.query([0xBE], 9, addr=addr2)
        pp = gex.PayloadParser(data)
        b = pp.i16() * 0.0625
        return a, b

    while True:
        (a, b) = meas2(6558392391241695016, 1802309978572980008)
        # a = meas(6558392391241695016)
        # b = meas(1802309978572980008)
        print("in: %.2f °C, out: %f °C" % (a, b))



    # # search the bus for alarm
    # if False:
    #     ow = gex.OneWire(client, 'ow')
    #     print("Presence: ", ow.test_presence())
    #     print("Devices w alarm:", ow.search(alarm=True))
    #
    # # simple 1w check
    # if False:
    #     ow = gex.OneWire(client, 'ow')
    #     print("Presence: ", ow.test_presence())
    #     print("ROM: 0x%016x" % ow.read_address())
    #     print("Scratch:", ow.query([0xBE], rcount=9, addr=0x7100080104c77610, as_array=True))
    #
    # # testing ds1820 temp meas without polling
    # if False:
    #     ow = gex.OneWire(client, 'ow')
    #     print("Presence: ", ow.test_presence())
    #     print("Starting measure...")
    #     ow.write([0x44])
    #     time.sleep(1)
    #     print("Scratch:", ow.query([0xBE], 9))
    #
    # # testing ds1820 temp meas with polling
    # if False:
    #     ow = gex.OneWire(client, 'ow')
    #     print("Presence: ", ow.test_presence())
    #     print("Starting measure...")
    #     ow.write([0x44])
    #     ow.wait_ready()
    #     data = ow.query([0xBE], 9)
    #
    #     pp = gex.PayloadParser(data)
    #
    #     temp = pp.i16()/2.0
    #     th = pp.i8()
    #     tl = pp.i8()
    #     reserved = pp.i16()
    #     remain = float(pp.u8())
    #     perc = float(pp.u8())
    #
    #     realtemp = temp - 0.25+(perc-remain)/perc
    #     print("Temperature = %f °C (th %d, tl %d)" % (realtemp, th, tl))
