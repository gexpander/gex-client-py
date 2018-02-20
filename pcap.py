import time

import gex

with gex.Client(gex.TrxRawUSB()) as client:
    fcap = gex.FCAP(client, 'fcap')

    fcap.stop()
    fcap.indirect_start()

    while True:
        time.sleep(1)
        print(fcap.indirect_read())
        #print(fcap.indirect_burst(3, timeout=20))

    # print(fcap.indirect_burst(10, timeout=20))


