#!/bin/env python3
import random

import gex
import time

# This is an adaptation of the micro dot phat library
# - the only change needed was replacing the smbus class with the GEX unit driver

ADDR = 0x61
MODE = 0b00011000
OPTS = 0b00001110 # 1110 = 35mA, 0000 = 40mA

CMD_BRIGHTNESS = 0x19
CMD_MODE = 0x00
CMD_UPDATE = 0x0C
CMD_OPTIONS = 0x0D

CMD_MATRIX_1 = 0x01
CMD_MATRIX_2 = 0x0E

MATRIX_1 = 0
MATRIX_2 = 1

class NanoMatrix:
    '''
    _BUF_MATRIX_1 = [ # Green
#Col   1 2 3 4 5
    0b00000000, # Row 1
    0b00000000, # Row 2
    0b00000000, # Row 3
    0b00000000, # Row 4
    0b00000000, # Row 5
    0b00000000, # Row 6
    0b10000000, # Row 7, bit 8 =  decimal place
    0b00000000
]
    _BUF_MATRIX_2 = [ # Red
#Row 8 7 6 5 4 3 2 1
    0b01111111, # Col 1, bottom to top
    0b01111111, # Col 2
    0b01111111, # Col 3
    0b01111111, # Col 4
    0b01111111, # Col 5
    0b00000000,
    0b00000000,
    0b01000000  # bit 7, decimal place
]
    _BUF_MATRIX_1 = [0] * 8
    _BUF_MATRIX_2 = [0] * 8
'''

    def __init__(self, bus:gex.I2C, address=ADDR):
        self.address = address
        self._brightness = 127

        self.bus = bus

        self.bus.write_byte_data(self.address, CMD_MODE, MODE)
        self.bus.write_byte_data(self.address, CMD_OPTIONS, OPTS)
        self.bus.write_byte_data(self.address, CMD_BRIGHTNESS, self._brightness)

        self._BUF_MATRIX_1 = [0] * 8
        self._BUF_MATRIX_2 = [0] * 8

    def set_brightness(self, brightness):
        self._brightness = int(brightness * 127)
        if self._brightness > 127: self._brightness = 127

        self.bus.write_byte_data(self.address, CMD_BRIGHTNESS, self._brightness)

    def set_decimal(self, m, c):

        if m == MATRIX_1:
           if c == 1:
               self._BUF_MATRIX_1[6] |= 0b10000000
           else:
               self._BUF_MATRIX_1[6] &= 0b01111111

        elif m == MATRIX_2:

           if c == 1:
               self._BUF_MATRIX_2[7] |= 0b01000000
           else:
               self._BUF_MATRIX_2[7] &= 0b10111111

        #self.update()

    def set(self, m, data):
        for y in range(7):
            self.set_row(m, y, data[y])

    def set_row(self, m, r, data):
        for x in range(5):
            self.set_pixel(m, x, r, (data & (1 << (4-x))) > 0)

    def set_col(self, m, c, data):
        for y in range(7):
            self.set_pixel(m, c, y, (data & (1 << y)) > 0)

    def set_pixel(self, m, x, y, c):

        if m == MATRIX_1:
            if c == 1:
                self._BUF_MATRIX_1[y] |= (0b1 << x)
            else:
                self._BUF_MATRIX_1[y] &= ~(0b1 << x)
        elif m == MATRIX_2:
            if c == 1:
                self._BUF_MATRIX_2[x] |= (0b1 << y)
            else:
                self._BUF_MATRIX_2[x] &= ~(0b1 << y)

        #self.update()

    def clear(self, m):
        if m == MATRIX_1:
            self._BUF_MATRIX_1 = [0] * 8
        elif m == MATRIX_2:
            self._BUF_MATRIX_2 = [0] * 8

        self.update()

    def update(self):
        for x in range(10):
            try:
                self.bus.write_i2c_block_data(self.address, CMD_MATRIX_1, self._BUF_MATRIX_1)
                self.bus.write_i2c_block_data(self.address, CMD_MATRIX_2, self._BUF_MATRIX_2)

                self.bus.write_byte_data(self.address, CMD_UPDATE, 0x01)
                break
            except IOError:
                print("IO Error")




with gex.Client(gex.TrxRawUSB()) as client:
    bus = gex.I2C(client, 'i2c')

    n1 = NanoMatrix(bus, 0x61)
    n2 = NanoMatrix(bus, 0x62)
    n3 = NanoMatrix(bus, 0x63)

    n1.set_pixel(0, 0, 0, 1)
    n1.set_pixel(0, 4, 0, 1)
    n1.set_pixel(0, 0, 6, 1)
    n1.set_pixel(0, 4, 6, 1)

    n1.set_pixel(1, 0, 0, 1)
    n1.set_pixel(1, 4, 0, 1)
    n1.set_pixel(1, 0, 3, 1)
    n1.set_pixel(1, 4, 3, 1)

    n2.set_pixel(0, 0, 2, 1)
    n2.set_pixel(0, 4, 2, 1)
    n2.set_pixel(0, 0, 5, 1)
    n2.set_pixel(0, 4, 5, 1)

    n2.set_pixel(1, 0, 0, 1)
    n2.set_pixel(1, 4, 0, 1)
    n2.set_pixel(1, 0, 6, 1)
    n2.set_pixel(1, 4, 6, 1)


    n3.set_pixel(0, 1, 0, 1)
    n3.set_pixel(0, 3, 0, 1)
    n3.set_pixel(0, 1, 6, 1)
    n3.set_pixel(0, 3, 6, 1)

    n3.set_pixel(1, 1, 1, 1)
    n3.set_pixel(1, 3, 1, 1)
    n3.set_pixel(1, 1, 5, 1)
    n3.set_pixel(1, 3, 5, 1)

    n1.update()
    n2.update()
    n3.update()

    b1 = 64
    b2 = 64
    b3 = 64

    while True:
        b1 += random.randint(-20, 15)
        b2 += random.randint(-20, 18)
        b3 += random.randint(-15, 13)

        if b1 < 0: b1 = 0
        if b2 < 0: b2 = 0
        if b3 < 0: b3 = 0
        if b1 > 127: b1 = 127
        if b2 > 127: b2 = 127
        if b3 > 127: b3 = 127

        n1.set_brightness(b1)
        n2.set_brightness(b2)
        n3.set_brightness(b3)

        time.sleep(0.05)
