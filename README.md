# Python client for GEX

This is the primary GEX front-end for user scripting.

GEX configuration can be persisted on-chip or loaded dynamically using 
the client from a INI file or string.

A sample GEX script could look like this:

```python

#!/bin/env python3
import time
import gex

client = gex.Client()

led = gex.Pin(client, 'LED')

for i in range(0,10):
    led.toggle()
    time.sleep(.1)

```

The client instance can be used to send control commands directly, bypassing the unit drivers.
Writing new unit drivers is simple and straightforward. See any of the existing units for reference.

