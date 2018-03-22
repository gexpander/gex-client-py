import time

import gex
import sx_fsk as sx


# this is a demo with two NRF24L01+ modules connected to SPI and some GPIO.
# using the ESB function.

class Nrf:
    def __init__(self, ce: gex.DOut, irq: gex.DIn, spi: gex.SPI, num):
        self.snum = num
        self.ce = ce
        self.irq = irq
        self.spi = spi

    def rd(self, addr, count=1):
        # addr 0-31
        return self.spi.query(self.snum, [addr&0x1F], rlen=count)

    def wr(self, addr, vals):
        if type(vals) == int:
            vals = [vals]

        # addr 0-31
        ba = bytearray()
        ba.append(addr | 0x20)
        ba.extend(vals)
        self.spi.write(self.snum, ba)

    def rd_payload(self, count):
        """ Read a received payload """
        return self.spi.query(self.snum, [0x61], rlen=count)

    def wr_payload(self, pld):
        """ Write a payload """
        ba = bytearray()
        ba.append(0xA0)
        ba.extend(pld)
        self.spi.write(self.snum, ba)

    def flush_tx(self):
        self.spi.write(self.snum, [0xE1])

    def flush_rx(self):
        self.spi.write(self.snum, [0xE2])

    def reuse_tx_pld(self):
        self.spi.write(self.snum, [0xE3])

    def get_pld_len(self):
        """ Read length of the first Rx payload in the FIFO - available only if dyn len enabled """
        return self.spi.query(self.snum, [0x60], rlen=1)[0]

    def wr_ack_payload(self, pipe, pld):
        """ Write a payload to be attached to the next sent ACK """
        ba = bytearray()
        ba.append(0xA8|(pipe&0x7))
        ba.extend(pld)
        self.spi.write(self.snum, ba)

    def wr_payload_noack(self, pld):
        """ Send a payload without ACK """
        ba = bytearray()
        ba.append(0xB0)
        ba.extend(pld)
        self.spi.write(self.snum, ba)

    def status(self):
        """ Send a payload without ACK """
        return self.spi.query(self.snum, [0xFF], rlen=1, rskip=0)[0]


with gex.Client(gex.TrxRawUSB()) as client:
    spi = gex.SPI(client, 'spi')
    ce = gex.DOut(client, 'ce')
    irq = gex.DIn(client, 'irq')

    a = Nrf(ce, irq, spi, 0)
    b = Nrf(ce, irq, spi, 1)
    a.flush_tx()
    a.flush_rx()
    b.flush_tx()
    b.flush_rx()

    # transmit demo
    # a is PTX, b is PRX
    ce.clear(0b11)

    # a_adr = [0xA1,0xA2,0xA3,0xA4,0x01]
    b_pipe0_adr = [0xA1, 0xA2, 0xA3, 0xA4, 0x02]

    # --- Configure A for Tx of a 32-long payload ---

    # PWR DN - simulate reset
    a.wr(0x00, 0)
    b.wr(0x00, 0)
    time.sleep(0.001)

    a.wr(0x00, 0b00001010) # set PWR_ON=1, EN_CRC=1, all irq enabled
    a.wr_payload([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31])

    chnl = 5

    # Set B's address as target and also pipe 0 Rx (used for ack)
    a.wr(0x10, b_pipe0_adr) # target addr
    a.wr(0x0A, b_pipe0_adr) # pipe 0 rx addr for ACK
    a.wr(0x04, 0b00101111) # configure retransmit
    a.wr(0x05, chnl)

    # --- Configure B for Rx ---

    b.wr(0x00, 0b00001011)  # set PWR_ON=1, PRIM_RX=1, EN_CRC=1, all irq enabled
    b.wr(0x02,   0b000001)  # enable pipe 0
    b.wr(0x11, 32) # set pipe 0 len to 11
    b.wr(0x0A, b_pipe0_adr) # set pipe 0's address
    b.wr(0x05, chnl)

    ce.set(0b10) # CE high for B
    time.sleep(0.01)

    ce.pulse_us(us=10, pins=0b01) # Pulse A's CE
    #
    # testing B's FIFO by sending another payload...
    a.wr_payload([0xFF, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30])
    ce.pulse_us(us=20, pins=0b01) # Pulse A's CE

    time.sleep(0.01)

    print("A's status after Tx: %02x" % a.status())
    print("B's status after Tx: %02x" % b.status())

    ce.clear(0b11)

    # read the two payloads
    print(b.rd_payload(32))
    print(b.rd_payload(32))
