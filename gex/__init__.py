#!/usr/bin/env python3

import serial

from gex.PayloadParser import PayloadParser
from gex.TinyFrame import TinyFrame, TF_Msg

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


class Gex:
    """ GEX client """

    def __init__(self, port='/dev/ttyACM0', timeout=0.3):
        """ Set up the client. timeout - timeout for waiting for a response. """
        self.port = port
        self.serial = serial.Serial(port=port, timeout=timeout)
        self.tf = TinyFrame()
        self.tf.write = self._write

        # test connection
        resp = self.query_raw(type=MSG_PING)
        print("GEX connected, version string: %s" % resp.data.decode('utf-8'))

        self.load_units()

    def load_units(self):
        """ Load a list of unit names and callsigns for look-up """
        resp = self.query_raw(type=MSG_LIST_UNITS)
        pp = PayloadParser(resp.data)
        count = pp.u8()

        self.unit_lu = {}

        for n in range(0,count):
            cs = pp.u8()
            name = pp.str()
            type = pp.str()

            print("- Found unit \"%s\" (type %s) @ callsign %d" % (name, type, cs))
            self.unit_lu[name] = {
                'callsign': cs,
                'type': type,
            }

    def get_callsign(self, name, type = None):
        """ Find unit by name and type """
        u = self.unit_lu[name]

        if type is not None:
            if u['type'] != type:
                raise Exception("Unit %s is not type %s (is %s)" % (name, type, u['type']))

        return u['callsign']

    def _write(self, data):
        self.serial.write(data)
        pass

    def poll(self, attempts=10):
        """ Read messages sent by GEX """

        first = True
        while attempts > 0:
            rv = bytearray()

            # Blocking read with a timeout
            if first:
                rv.extend(self.serial.read(1))
                first = False

            # Non-blocking read of the rest
            rv.extend(self.serial.read(self.serial.in_waiting))

            if 0 == len(rv):
                # nothing was read
                if self.tf.ps == 'SOF':
                    # TF is in base state, we're done
                    return
                else:
                    # Wait for TF to finish the frame
                    attempts -= 1
                    first = True
            else:
                self.tf.accept(rv)

    def _send(self, type, id=None, pld=None, listener=None):
        self.tf.query(type=type, pld=pld, id=id, listener=listener)

    def send(self, cs, cmd, id=None, pld=None, listener=None):
        """ Send a command to a unit """
        if cs is None:
            return self._send(type=cmd, id=id, pld=pld, listener=listener)

        if pld is None:
            pld = b''

        buf = bytearray([cs, cmd])
        buf.extend(pld)
        self._send(type=MSG_UNIT_REQUEST, id=id, pld=buf, listener=listener)

    def query(self, cs, cmd, id=None, pld=None):
        """ Query a unit """

        self._theframe = None

        def lst(tf, frame):
            self._theframe = frame

        self.send(cs, cmd, id=id, pld=pld, listener=lst)
        self.poll()

        if self._theframe is None:
            raise Exception("No response to query")

        return self._theframe

    def query_raw(self, type, id=None, pld=None):
        """ Query GEX, without addressing a unit """
        return self.query(cs=None, cmd=type, id=id, pld=pld)

    def send_raw(self, type, id=None, pld=None):
        """ Send to GEX, without addressing a unit """
        return self.send(cs=None, cmd=type, id=id, pld=pld)
