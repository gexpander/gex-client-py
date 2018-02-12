#!/bin/env python3
import time

import numpy as np
from matplotlib import pyplot as plt

import gex

transport = gex.TrxRawUSB(sn='0029002F-42365711-32353530')
#transport = gex.TrxSerialSync(port='/dev/ttyACM0')

with gex.Client(transport) as client:
    #
    # if True:
    #     s = client.ini_read()
    #     print(s)
    #     client.ini_write(s)

    if False:
        adc = gex.ADC(client, 'adc')
        print("Enabled channels:", adc.get_channels())

        adc.set_smoothing_factor(0.9)

        while True:
            raw = adc.read_raw()
            smooth = adc.read_smooth()
            print("IN1 = %d (%.2f), Tsens = %d (%.2f), Vrefint = %d (%.2f)" % (raw[1], smooth[1],
                                                                               raw[16], smooth[16],
                                                                               raw[17], smooth[17]))
            time.sleep(0.5)

    if True:
        adc = gex.ADC(client, 'adc')

        adc.set_active_channels([1])
        fs = adc.set_sample_rate(1000)

        data = adc.capture(1000)

        if data is not None:
            plt.plot(data, 'r-', lw=1)
            plt.show()
        else:
            print("Nothing rx")


        # for r in range(0,8):
        #     adc.set_sample_time(r)
        #     data = adc.capture(10000)
        #     print("sr = %d" % r)
        #     std = np.std(data)
        #     print(std)


        #
        # global data
        # data = None
        #
        # def capture(rpt):
        #     global data
        #     print("trig'd, %s" % rpt)
        #     data = rpt.data
        # #
        # # adc.setup_trigger(channel=1,
        # #                   level=700,
        # #                   count=20000,
        # #                   pretrigger=100,
        # #                   auto=False,
        # #                   edge="falling",
        # #                   holdoff=200,
        # #                   handler=capture)
        #
        # # adc.arm()
        #
        # data = adc.capture(1000)
        #
        # if data is not None:
        #     plt.plot(data, 'r.', lw=1)
        #     plt.show()
        # else:
        #     print("Nothing rx")

        # plt.magnitude_spectrum(data[:,0], Fs=fs, scale='dB', color='C1')
        # plt.show()

        # def lst(data):
        #     if data is not None:
        #         print("Rx OK") #data
        #     else:
        #         print("Closed.")

        # adc.stream_start(lst)
        # time.sleep(3)
        # adc.stream_stop()
        # print("Done.")




        # time.sleep(.1)
        # print(adc.get_sample_rate())
        # time.sleep(.1)

        # adc.stream_stop()
        # time.sleep(5)

        # print(adc.capture(200, 5))

        # adc.setup_trigger(channel=1,
        #                   level=700,
        #                   count=100,
        #                   pretrigger=15,
        #                   auto=True,
        #                   edge="falling",
        #                   holdoff=200,
        #                   handler=lambda rpt: print("Report: %s" % rpt))
        #
        # print("Armed")
        # adc.arm()
        # print("Sleep...")
        # # adc.force()
        # #
        # # # adc.disarm()
        # time.sleep(5)
        # adc.disarm()

        # print(adc.capture(200, 50))

        # adc.stream_start(lambda data: print(data))
        # time.sleep(20)
        # adc.stream_stop()


        # print(adc.read_raw())

        # time.sleep(1)
        # print("Rx: ", resp)
        # adc.abort()

    if False:
        s = client.ini_read()
        print(s)
        client.ini_write(s)

    # search the bus
    if False:
        ow = gex.OneWire(client, 'ow')
        print("Devices:", ow.search())

    # search the bus for alarm
    if False:
        ow = gex.OneWire(client, 'ow')
        print("Presence: ", ow.test_presence())
        print("Devices w alarm:", ow.search(alarm=True))

    # simple 1w check
    if False:
        ow = gex.OneWire(client, 'ow')
        print("Presence: ", ow.test_presence())
        print("ROM: 0x%016x" % ow.read_address())
        print("Scratch:", ow.query([0xBE], rcount=9, addr=0x7100080104c77610, as_array=True))

    # testing ds1820 temp meas without polling
    if False:
        ow = gex.OneWire(client, 'ow')
        print("Presence: ", ow.test_presence())
        print("Starting measure...")
        ow.write([0x44])
        time.sleep(1)
        print("Scratch:", ow.query([0xBE], 9))

    # testing ds1820 temp meas with polling
    if False:
        ow = gex.OneWire(client, 'ow')
        print("Presence: ", ow.test_presence())
        print("Starting measure...")
        ow.write([0x44])
        ow.wait_ready()
        data = ow.query([0xBE], 9)

        pp = gex.PayloadParser(data)

        temp = pp.i16()/2.0
        th = pp.i8()
        tl = pp.i8()
        reserved = pp.i16()
        remain = float(pp.u8())
        perc = float(pp.u8())

        realtemp = temp - 0.25+(perc-remain)/perc
        print("Temperature = %f °C (th %d, tl %d)" % (realtemp, th, tl))


    if False:
        buf = client.bulk_read(gex.MSG_INI_READ)
        print(buf.decode('utf-8'))

        pb = gex.PayloadBuilder()
        pb.u32(len(buf))

        client.bulk_write(gex.MSG_INI_WRITE, pld=pb.close(), bulk=buf)

    if False:
        leds = gex.DOut(client, 'strip')

        nn = 3
        for i in range(0,20):
            leds.write(nn)
            time.sleep(.05)
            nn<<=1
            nn|=(nn&0x40)>>6
            nn=nn&0x3F
        leds.clear(0xFF)

    if False:
        leds = gex.DOut(client, 'bargraph')

        for i in range(0,0x41):
            leds.write(i&0x3F)
            time.sleep(.1)

    if False:
        leds = gex.DOut(client, 'TST')

        for i in range(0, 0x41):
            #leds.write(i & 0x3F)
            leds.toggle(0xFF)
            time.sleep(.1)

    if False:
        btn = gex.DIn(client, 'btn')
        strip = gex.DOut(client, 'strip')

        for i in range(0, 10000):
            b = btn.read()
            strip.write((b << 2) | ((~b) & 1))
            time.sleep(.02)

    if False:
        neo = gex.Neopixel(client, 'npx')

        print('We have %d neopixels.\n' % neo.get_len())

        #neo.load([0xF0F0F0,0,0,0xFF0000])

        # generate a little animation...
        for i in range(0,512):
            j = i if i < 256 else 255-(i-256)
            neo.load([0x660000+j, 0x3300FF-j, 0xFFFF00-(j<<8), 0x0000FF+(j<<8)-j])
            time.sleep(.001)

        neo.load([0,0,0,0])

    if False:
        i2c = gex.I2C(client, 'i2c')

        # i2c.write(0x76, payload=[0xD0])
        # print(i2c.read(0x76, count=1))

        print(i2c.read_reg(0x76, 0xD0))
        print("%x" % i2c.read_reg(0x76, 0xF9, width=3, endian='big'))

        i2c.write_reg(0x76, 0xF4, 0xFA)
        print(i2c.read_reg(0x76, 0xF4))

    if False:
        spi = gex.SPI(client, 'spi')
        spi.multicast(1, [0xDE, 0xAD, 0xBE, 0xEF])
        print(spi.query(0, [0xDE, 0xAD, 0xBE, 0xEF], rlen=4, rskip=1))#

    if False:
        usart = gex.USART(client, 'serial')
        usart.listen(lambda x: print("RX >%s<" % x))
        for i in range(0,100):
            #             Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque ac bibendum lectus, ut pellentesque sem. Suspendisse ultrices felis eu laoreet luctus. Nam sollicitudin ultrices leo, ac condimentum enim vulputate quis. Suspendisse cursus tortor nibh, ac consectetur eros dapibus quis. Aliquam erat volutpat. Duis sagittis eget nunc nec condimentum. Aliquam erat volutpat. Phasellus molestie sem vitae quam semper convallis.

            usart.write("""_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n""".encode(), sync=True)

            # time.sleep(.001)

    if False:
        usart = gex.USART(client, 'serial')
        usart.listen(lambda x: print(x, end='',flush=True))
        while True:
            client.poll()

    if False:
        print(client.ini_read())

        trig = gex.DIn(client, 'trig')
        print(trig.read())

        # Two pins are defined, PA10 and PA7. PA10 is the trigger, in the order from smallest to highest number 1
        trig.arm(0b10)
        trig.on_trigger(0b10, lambda snap,ts: print("snap 0x%X, ts %d" % (snap,ts)))

        while True:
            client.poll()

    #
    # for n in range(0,100):
    #     print(n)
    #     s = client.ini_read()
    #     client.ini_write(s)
