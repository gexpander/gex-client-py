#!/bin/env python3
import time
import gex

client = gex.Client(timeout=1.5)

#print(client.ini_read())

if False:
    s = client.ini_read()
    print(s)
    client.ini_write(s)

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

if True:
    usart = gex.USART(client, 'serial')
    usart.listen(lambda x: print("RX >%s<" % x))
    for i in range(0,100):
        #             Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque ac bibendum lectus, ut pellentesque sem. Suspendisse ultrices felis eu laoreet luctus. Nam sollicitudin ultrices leo, ac condimentum enim vulputate quis. Suspendisse cursus tortor nibh, ac consectetur eros dapibus quis. Aliquam erat volutpat. Duis sagittis eget nunc nec condimentum. Aliquam erat volutpat. Phasellus molestie sem vitae quam semper convallis.

        usart.write("""_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n_.-"_.-"_.-"_.-"_.-"_.-"_.-"_.\r\n""".encode(), sync=True)

        # time.sleep(.001)

if False:
    usart = gex.USART(client, 'serial')
    usart.listen(lambda x: print("RX >%s<" % x))
    while True:
        client.poll()
        time.sleep(.01)
#
# for n in range(0,100):
#     print(n)
#     s = client.ini_read()
#     client.ini_write(s)
