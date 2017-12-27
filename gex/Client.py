import serial
import gex
from gex import TinyFrame, PayloadParser, TF, PayloadBuilder


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

    def ini_read(self):
        """ Read the settings INI file """
        buffer = self.bulk_read(cs=None, cmd=gex.MSG_INI_READ)
        return buffer.decode('utf-8')

    def ini_write(self, buffer):
        """ Read the settings INI file """
        if type(buffer) == str:
            buffer = buffer.encode('utf-8')

        self.bulk_write(cs=None, cmd=gex.MSG_INI_WRITE, bulk=buffer)

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
        """ Send a command to a unit. If cs is None, cmd is used as message type """
        if cs is None:
            return self.tf.query(type=cmd, id=id, pld=pld, listener=listener)

        if pld is None:
            pld = b''

        buf = bytearray([cs, cmd])
        buf.extend(pld)
        self.tf.query(type=gex.MSG_UNIT_REQUEST, id=id, pld=buf, listener=listener)

    def query(self, cs, cmd, id=None, pld=None):
        """ Query a unit. If cs is None, cmd is used as message type """

        self._theframe = None

        def lst(tf, frame):
            self._theframe = frame
            return TF.CLOSE

        self.send(cs, cmd, id=id, pld=pld, listener=lst)
        self.poll()

        if self._theframe is None:
            raise Exception("No response to query")

        if self._theframe.type == gex.MSG_ERROR:
            raise Exception("Error response: %s" % self._theframe.data.decode('utf-8'))

        return self._theframe

    def query_raw(self, type, id=None, pld=None):
        """ Query GEX, without addressing a unit """
        return self.query(cs=None, cmd=type, id=id, pld=pld)

    def send_raw(self, type, id=None, pld=None):
        """ Send to GEX, without addressing a unit """
        return self.send(cs=None, cmd=type, id=id, pld=pld)

    def bulk_read(self, cs, cmd, id=None, pld=None, chunk=1024):
        """ Perform a bulk read. If cs is None, cmd is used as message type """

        offer = self.query(cs=cs, cmd=cmd, id=id, pld=pld)
        if offer.type != gex.MSG_BULK_READ_OFFER:
            raise Exception("Bulk read rejected! %s" % offer.data.decode('utf-8'))

        # parse the offer
        pp = PayloadParser(offer.data)
        total = pp.u32()
        # we don't need to worry much about the total size,
        # this is for static buffers in C.

        at = 0
        buffer = bytearray()
        while at < total:
            # Ask for a chunk
            pb = PayloadBuilder()
            pb.u32(chunk)

            pollrv = self.query_raw(type=gex.MSG_BULK_READ_POLL, id=offer.id, pld=pb.close())

            if pollrv.type in [gex.MSG_BULK_DATA, gex.MSG_BULK_END]:
                buffer.extend(pollrv.data)
                at += len(pollrv.data)
                if pollrv.type == gex.MSG_BULK_END:
                    break
            else:
                raise Exception("Unexpected bulk frame type %d" % pollrv.type)

        return buffer

    def bulk_write(self, cs, cmd, bulk, id=None, pld=None):
        """
        Perform a bulk write. If cs is None, cmd is used as message type.
        bulk is the data to write.
        """

        offer = self.query(cs=cs, cmd=cmd, id=id, pld=pld)
        if offer.type != gex.MSG_BULK_WRITE_OFFER:
            raise Exception("Bulk write rejected! %s" % offer.data.decode('utf-8'))

        # parse the offer
        pp = PayloadParser(offer.data)
        max_size = pp.u32()
        max_chunk = pp.u32()

        total = len(bulk)

        if max_size < total:
            # announce we changed our mind and won't write anything
            self.send_raw(type=gex.MSG_BULK_ABORT, id=offer.id)
            raise Exception("Bulk write not possible, not enough space (needed %d bytes, max %d)" % (total, max_size))

        at = 0
        while at < total:
            chunklen = min(max_chunk, total - at)
            # Send data
            rv = self.query_raw(type=gex.MSG_BULK_DATA if chunklen == max_chunk else gex.MSG_BULK_END,
                                id=offer.id,
                                pld=bulk[at:at+chunklen])

            if rv.type != gex.MSG_SUCCESS:
                raise Exception("Unexpected bulk frame type %d" % rv.type)

            at += chunklen
