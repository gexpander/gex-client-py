import time

import gex

with gex.Client(gex.TrxRawUSB()) as client:
    tsc = gex.TOUCH(client, 'tsc')

    print("There are %d touch channels." % tsc.get_channel_count())

    tsc.set_button_thresholds([1225, 1440, 1440])

    tsc.listen(0, lambda state, ts: print("Pad 1: %d" % state))
    tsc.listen(1, lambda state, ts: print("Pad 2: %d" % state))
    tsc.listen(2, lambda state, ts: print("Pad 3: %d" % state))

    while True:
        print(tsc.read())
        time.sleep(0.5)
