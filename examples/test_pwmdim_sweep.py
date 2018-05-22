import time

import gex

# pwm frequency sweep

with gex.Client(gex.TrxRawUSB()) as client:
    pwm = gex.PWMDim(client, 'dim')

    pwm.start()
    pwm.set_duty_single(1, 500)
    for i in range(2000, 200, -15):
        pwm.set_frequency(i)
        time.sleep(0.05)

    pwm.stop()

