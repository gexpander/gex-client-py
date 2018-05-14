#!/bin/env python3
import gex
import time

ADDR = 0x61
MODE = 0b00011000
OPTS = 0b00001110 # 1110 = 35mA, 0000 = 40mA

CMD_BRIGHTNESS = 0x19
CMD_MODE = 0x00
CMD_UPDATE = 0x0C
CMD_OPTIONS = 0x0D

CMD_MATRIX_1 = 0x01
CMD_MATRIX_2 = 0x0E

with gex.Client(gex.TrxRawUSB()) as client:
    bus = gex.I2C(client, 'i2c')
    addr = 0x61
    bus.write_reg(addr, CMD_MODE, MODE)
    bus.write_reg(addr, CMD_OPTIONS, OPTS)
    bus.write_reg(addr, CMD_BRIGHTNESS, 64)

    bus.write(addr, [CMD_MATRIX_1,
                     0xAA,0x55,0xAA,0x55,
                     0xAA,0x55,0xAA,0x55,
                     ])

    bus.write(addr, [CMD_MATRIX_2,
                     0xFF, 0, 0xFF, 0,
                     0xFF, 0, 0xFF, 0,
                     ])

    bus.write_reg(addr, CMD_UPDATE, 0x01)