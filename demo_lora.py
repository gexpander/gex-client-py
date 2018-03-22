import time

import gex
import sx_fsk as sx


# we're demonstrating the use of the GFSK mode of the SX1278
# this is an example of how GEX can be used to control a peripheral module - in this case evaluating
#  it for use in GEX remote


class LoRa:
    def __init__(self,
                 rst: gex.DOut,
                 spi: gex.SPI, ssnum):
        self.ss = ssnum
        self.rst = rst
        self.spi = spi

    def reset(self):
        self.rst.pulse_us(100, active=False)
        time.sleep(0.005)

    def rd(self, addr):
        return self.spi.query(self.ss, [addr], 1)[0]

    def wr(self, addr, value):
        self.spi.write(self.ss, [addr | 0x80, value])

    def rds(self, start, count=1):
        return self.spi.query(self.ss, [start], count)

    def wrs(self, start, values):
        ba = bytearray()
        ba.append(start | 0x80)
        ba.extend(values)
        self.spi.write(self.ss, ba)

    def rmw(self, addr, keep, set):
        """ rmw, first and-ing the register with mask and then oring with set """
        val = self.rd(addr)
        self.wr(addr, (val & keep) | set)

    def waitModeSwitch(self):
        while 0 == (self.rd(sx.REG_IRQFLAGS1) & sx.RF_IRQFLAGS1_MODEREADY):
            time.sleep(0.001)

    def waitSent(self):
        while 0 == (self.rd(sx.REG_IRQFLAGS2) & sx.RF_IRQFLAGS2_PACKETSENT):
            time.sleep(0.001)

    def fsk_set_defaults(self):
        # Set default values (semtech patches: * in DS)
        self.rmw(sx.REG_RXCONFIG,
                 sx.RF_RXCONFIG_RXTRIGER_MASK,
                 sx.RF_RXCONFIG_RXTRIGER_PREAMBLEDETECT)

        self.wr(sx.REG_PREAMBLEDETECT,
             sx.RF_PREAMBLEDETECT_DETECTOR_ON |
             sx.RF_PREAMBLEDETECT_DETECTORSIZE_2 |
             sx.RF_PREAMBLEDETECT_DETECTORTOL_10)

        self.rmw(sx.REG_OSC, sx.RF_OSC_CLKOUT_MASK, sx.RF_OSC_CLKOUT_OFF)

        self.rmw(sx.REG_FIFOTHRESH,
                 sx.RF_FIFOTHRESH_TXSTARTCONDITION_MASK,
                 sx.RF_FIFOTHRESH_TXSTARTCONDITION_FIFONOTEMPTY)

        self.rmw(sx.REG_IMAGECAL,
                 sx.RF_IMAGECAL_AUTOIMAGECAL_MASK,
                 sx.RF_IMAGECAL_AUTOIMAGECAL_OFF)

    def configure_for_fsk(self, address):
        self.rmw(sx.REG_OPMODE,
              sx.RF_OPMODE_LONGRANGEMODE_MASK & sx.RF_OPMODE_MODULATIONTYPE_MASK & sx.RF_OPMODE_MASK,
                 sx.RF_OPMODE_LONGRANGEMODE_OFF |
                 sx.RF_OPMODE_MODULATIONTYPE_FSK |
                 sx.RF_OPMODE_STANDBY)
        self.waitModeSwitch()

        self.fsk_set_defaults()
        self.wr(sx.REG_NODEADRS, address)
        self.wr(sx.REG_BROADCASTADRS, 0xFF)
        # use whitening and force address matching
        self.rmw(sx.REG_PACKETCONFIG1,
              sx.RF_PACKETCONFIG1_DCFREE_MASK & sx.RF_PACKETCONFIG1_ADDRSFILTERING_MASK,
                 sx.RF_PACKETCONFIG1_DCFREE_WHITENING |
                 sx.RF_PACKETCONFIG1_ADDRSFILTERING_NODEBROADCAST)

        self.wr(sx.REG_RXCONFIG,
                sx.RF_RXCONFIG_AFCAUTO_ON |
                sx.RF_RXCONFIG_AGCAUTO_ON |
                sx.RF_RXCONFIG_RXTRIGER_PREAMBLEDETECT)

        XTAL_FREQ = 32000000
        FREQ_STEP = 61.03515625
        FSK_FDEV = 60000  # Hz NOTE: originally: 25000, seems to help increasing
        FSK_DATARATE = 200000  # bps - originally 50000

        MAX_RFPOWER = 0 # 0-7 boost - this doesnt seem to have a huge impact

        FSK_PREAMBLE_LENGTH = 5  # Same for Tx and Rx

        fdev = round(FSK_FDEV / FREQ_STEP)
        self.wr(sx.REG_FDEVMSB, fdev >> 8)
        self.wr(sx.REG_FDEVLSB, fdev & 0xFF)

        datarate = round(XTAL_FREQ / FSK_DATARATE)
        print("dr=%d"%datarate)
        self.wr(sx.REG_BITRATEMSB, datarate >> 8)
        self.wr(sx.REG_BITRATELSB, datarate & 0xFF)

        preamblelen = FSK_PREAMBLE_LENGTH
        self.wr(sx.REG_PREAMBLEMSB, preamblelen >> 8)
        self.wr(sx.REG_PREAMBLELSB, preamblelen & 0xFF)

        # bandwidths - 1 MHz
        self.wr(sx.REG_RXBW, 0x0A) # FSK_BANDWIDTH
        self.wr(sx.REG_AFCBW, 0x0A) # FSK_AFC_BANDWIDTH

        # max payload len to rx
        self.wr(sx.REG_PAYLOADLENGTH, 0xFF)

        self.rmw(sx.REG_PARAMP, 0x9F, 0x40) # enable gauss 0.5

        # pick the sync word size
        self.rmw(sx.REG_SYNCCONFIG,
                 sx.RF_SYNCCONFIG_SYNCSIZE_MASK,
                 sx.RF_SYNCCONFIG_SYNCSIZE_3)

        # sync word (network ID)
        self.wrs(sx.REG_SYNCVALUE1, [
            0xe7, 0x3d, 0xfa, 0x01, 0x5e, 0xa1, 0xc9, 0x98 # something random
        ])

        # enable LNA boost (?)
        self.rmw(sx.REG_LNA,
                 sx.RF_LNA_BOOST_MASK,
                 sx.RF_LNA_BOOST_ON)

        # experiments with the pa config
        self.rmw(sx.REG_PACONFIG,
                 sx.RF_PACONFIG_PASELECT_MASK|0x8F, # max power mask
                 sx.RF_PACONFIG_PASELECT_PABOOST | MAX_RFPOWER<<4)

        # we could also possibly adjust the Tx power



with gex.Client(gex.TrxRawUSB()) as client:
    spi = gex.SPI(client, 'spi')
    rst1 = gex.DOut(client, 'rst1')
    rst2 = gex.DOut(client, 'rst2')

    a = LoRa(rst1, spi, 0)
    b = LoRa(rst2, spi, 1)

    # reset the two transceivers to ensure they start in a defined state
    a.reset()
    b.reset()

    # go to sleep mode, select FSK
    a.configure_for_fsk(0x33)
    b.configure_for_fsk(0x44)

    print("Devices configured")

    for j in range(0, 240):
        if(j>0 and j%60==0):
            print()

        # --- Send a message from 1 to 2 ---
        msg = [
            51, # len
            0x44, # address
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
            0, 1, 2, 3, 4, 5, 6, 7, 8, j
        ]

        a.wrs(sx.REG_FIFO, msg)

        b.rmw(sx.REG_OPMODE, sx.RF_OPMODE_MASK, sx.RF_OPMODE_RECEIVER)
        # time.sleep(0.005)

        # trigger A
        a.rmw(sx.REG_OPMODE, sx.RF_OPMODE_MASK, sx.RF_OPMODE_TRANSMITTER)
        a.waitModeSwitch()
        a.waitSent()
        # time.sleep(0.02)

        # print("a irq flags = ", ["0x%02x"%x for x in a.rds(sx.REG_IRQFLAGS1, 2)])
        # print("b irq flags = ", ["0x%02x"%x for x in b.rds(sx.REG_IRQFLAGS1, 2)])

        rxd = [b.rd(sx.REG_FIFO) for x in range(0,len(msg))]
        if rxd == msg:
            print("\x1b[32;1m+\x1b[0m", end="", flush=True)
        else:
            print("\x1b[31m-\x1b[0m", end="", flush=True)
        #
        # for i in range(0,8):
        #     print("0x%02x" % rxd[i],end=" ")
        # print()
        # print()
    print()

    # good night
    a.rmw(sx.REG_OPMODE, sx.RF_OPMODE_MASK, sx.RF_OPMODE_SLEEP)
    b.rmw(sx.REG_OPMODE, sx.RF_OPMODE_MASK, sx.RF_OPMODE_SLEEP)


