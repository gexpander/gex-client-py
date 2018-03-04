import time

import gex

with gex.Client(gex.TrxRawUSB()) as client:
    ser = gex.USART(client, 'ser')
    leds = gex.SIPO(client, 'leds')

    while True:
        ser.clear_buffer()
        ser.write([0xFF, 0x01, 0x86, 0, 0, 0, 0, 0, 0x79])
        data = ser.receive(9, decode=None)

        pp = gex.PayloadParser(data, endian="big").skip(2)
        ppm = pp.u16()
        
        # The LEDs are connected to two 595's, interleaved R,G,R,G...
        nl = (ppm-300)/1700.0
        print("%d ppm CO₂, numleds %f" % (ppm, nl*8))
        
        numb = 0
        for i in range(0,8):
          if nl >= i*0.125:
            if i < 3:
              numb |= 2<<(i*2)
            elif i < 6:
              numb |= 3<<(i*2)
            else:
              numb |= 1<<(i*2)
        
        leds.load([(numb&0xFF00)>>8,numb&0xFF])
        

        time.sleep(1)

