#!/bin/env python3
import gex

with gex.Client(gex.TrxRawUSB()) as client:
    # Neopixel strip
    strip = gex.Neopixel(client, 'npx')
    # Load RGB to the strip
    strip.load([0xFF0000, 0x00FF00, 0x0000FF, 0xFF00FF])
    #
    # # I2C bus
    # i2c = gex.I2C(client, 'i2c')
    # # Read device register
    # print(i2c.read_reg(address=0x76, reg=0xD0))
    # # Write value to a register
    # i2c.write_reg(address=0x76, reg=0xF4, value=0xFA)
    #
    # # SPI
    # spi = gex.SPI(client, 'spi')
    # # Query slave 0
    # print(spi.query(0, [0xAA, 0xBB, 0xCC, 0xDD], rlen=2, rskip=4))
    # # Write slaves 0 and 2
    # spi.multicast(0b101, [0xDE, 0xAD, 0xBE, 0xEF])
    #
    # # USART
    # usart = gex.USART(client, 'serial')
    # # Handle received data
    # usart.listen(lambda x: print(x, end='', flush=True))
    # # Write a string
    # usart.write("AHOJ\r\n")
    #
    # # Digital output (8 pins)
    # display = gex.DOut(client, 'display')
    # display.write(0b10110011)
    # display.toggle(0b00010010)

