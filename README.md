# Python client for GEX

This is the primary GEX front-end for user scripting. It may be used natively with python3,
or integrated in MATLAB through the Python call API.

## Installation

Add this library as a git submodule 'gex' to your project (or simply copy it there).

### Linux

You may want to create this file in `/etc/udev/rules.d/98-gex.rules` and add your user to 
the `plugdev` group.

```
SUBSYSTEM=="usb", ATTR{idVendor}=="1209", ATTR{idProduct}=="4c60", GROUP="plugdev", MODE="0660"
SUBSYSTEM=="usb", ATTR{idVendor}=="1209", ATTR{idProduct}=="4c61", GROUP="plugdev", MODE="0660"
```


### BSD

Not tested, may be similar to Linux


### Mac

Not tested


### Windows 8.1 and older

You need to attach the [STM32 Virtual COM Port Driver](http://www.st.com/en/development-tools/stsw-stm32102.html) 
to the GEX device using the Device Manager, if they want to use the Virtual COM port attachment 
method (the Serial transport options, see below).

Additionally, they may have to configure the Mass Storage endpoint to use the Mass Storage system driver,
because older Windows are not smart enough to figure it out (we're using the standard device class and 
everything, but still).

The Python scripts can be run with Cygwin, or the Windows Python port.


### Windows 10

It should Just Work™ without any special configuration needed.


## Example

A sample GEX script could look like this:

```python

#!/bin/env python3
import time
import gex

with gex.Client() as client:
  led = gex.DOut(client, 'led')
  for i in range(0,10):
    led.toggle()
    time.sleep(.1)

```

The client object can be used to send control commands directly, bypassing unit drivers.

Writing new unit drivers is simple, just extend the Unit class and add the unit-specific 
methods and logic.

## Transports

The CLient class takes a Transport instance as a constructor parameter. There are three
transports defined:

- `TrxSerialSync` - VCOM, blocking (with a polling loop)

- `TrxSerialThread` - VCOM, asynchronous

- `TrxRawUSB` - PyUSB, the default and usually the best transport 

  Pass the device serial ID as am argument to match it if you have multiple 
  GEX modules attached at once.

Additionally, either transport can be wrapped in `DongleAdapter` when the _Wireless Gateway_ 
dongle is used. The `TrxRawUSB` further needs the second argument, `remote`, set to true in 
this case, to look for devices with the Gateway vid:pid value 1209:4c61. 
GEX modules themselves have 1209:4c60.

