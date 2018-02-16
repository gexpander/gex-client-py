#!/usr/bin/env python3

from gex.PayloadBuilder import PayloadBuilder
from gex.PayloadParser import PayloadParser
from gex.TinyFrame import TinyFrame, TF_Msg, TF
from gex.Unit import Unit
from gex.Client import Client
from gex.transport import TrxRawUSB
from gex.transport import TrxSerialSync

# import all the units
from gex.units.DOut import DOut
from gex.units.DIn import DIn
from gex.units.Neopixel import Neopixel
from gex.units.I2C import I2C
from gex.units.SPI import SPI
from gex.units.USART import USART
from gex.units.OneWire import OneWire
from gex.units.ADC import ADC
from gex.units.SIPO import SIPO


# General, low level
MSG_SUCCESS = 0x00  # Generic success response; used by default in all responses; payload is transaction-specific
MSG_PING = 0x01  # Ping request (or response), used to test connection
MSG_ERROR = 0x02  # Generic failure response (when a request fails to execute)

MSG_BULK_READ_OFFER = 0x03  # Offer of data to read. Payload: u32 total len
MSG_BULK_READ_POLL = 0x04  # Request to read a previously announced chunk. Payload: u32 max chunk
MSG_BULK_WRITE_OFFER = 0x05  # Offer to receive data in a write transaction. Payload: u32 max size, u32 max chunk
MSG_BULK_DATA = 0x06  # Writing a chunk, or sending a chunk to master.
MSG_BULK_END = 0x07  # Bulk transfer is done, no more data to read or write.
#   Recipient shall check total len and discard it on mismatch. There could be a checksum ...
MSG_BULK_ABORT = 0x08  # Discard the ongoing transfer

# Unit messages
MSG_UNIT_REQUEST = 0x10  # Command addressed to a particular unit
MSG_UNIT_REPORT = 0x11  # Spontaneous report from a unit

# System messages
MSG_LIST_UNITS = 0x20  # Get all unit call-signs and names
MSG_INI_READ = 0x21  # Read the ini file via bulk
MSG_INI_WRITE = 0x22  # Write the ini file via bulk
MSG_PERSIST_SETTINGS = 0x23  # Write current settings to Flash
