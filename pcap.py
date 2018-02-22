import time

import gex

with gex.Client(gex.TrxRawUSB()) as client:
    fcap = gex.FCAP(client, 'fcap')

    fcap.stop()

    fcap.indirect_start()
    #
    time.sleep(2)
    print(fcap.indirect_read())

    # fcap.stop()
    # #print(fcap.indirect_burst(3, timeout=20))

    # r=fcap.indirect_burst(1000, timeout=5)
    # print(r)
    # print(r.period_raw)

    # fcap.configure(filter=0)

    # print(fcap.measure_pulse())

    # print(fcap.direct_burst(10))
    #
    # fcap.direct_start(1000, 0)
    # time.sleep(2)
    #
    # print(fcap.direct_read())
    #
    # fcap.counter_start()
    # time.sleep(1)
    # print(fcap.counter_clear())
    # time.sleep(1)
    # print(fcap.counter_read())
    # time.sleep(1)
    # print(fcap.counter_clear())
    # time.sleep(1)
    # print(fcap.counter_clear())


