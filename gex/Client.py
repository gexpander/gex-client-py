import serial
import gex
from gex import TinyFrame, PayloadParser

class Client:
    """ GEX client """

    def __init__(self, port='/dev/ttyACM0', timeout=0.3):
        """ Set up the client. timeout - timeout for waiting for a response. """
        self.port = port
        self.serial = serial.Serial(port=port, timeout=timeout)
        self.tf = TinyFrame()
        self.tf.write = self._write

        # test connection
        resp = self.query_raw(type=gex.MSG_PING)
        print("GEX connected, version string: %s" % resp.data.decode('utf-8'))

        self.load_units()

    def load_units(self):
        """ Load a list of unit names and callsigns for look-up """
        resp = self.query_raw(type=gex.MSG_LIST_UNITS)
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
        """ Write bytes to the serial port """
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

    def send(self, cs, cmd, id=None, pld=None, listener=None):
        """ Send a command to a unit """
        if cs is None:
            return self.tf.query(type=cmd, id=id, pld=pld, listener=listener)

        if pld is None:
            pld = b''

        buf = bytearray([cs, cmd])
        buf.extend(pld)
        self.tf.query(type=gex.MSG_UNIT_REQUEST, id=id, pld=buf, listener=listener)

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
