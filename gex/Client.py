import threading
import gex
import time
from gex import TinyFrame, PayloadParser, TF, PayloadBuilder, TF_Msg, transport

class EventReport:
    def __init__(self, msg:TF_Msg, cs:int, event:int, timestamp:int, payload):
        self.msg = msg
        self.callsign = cs
        self.code = event
        self.timestamp = timestamp
        self.payload = payload

class Client:
    """ GEX client """

    def __init__(self, transport, load_units=True):
        """
        Set up the client, looking up the GEX USB device using the S/N.
        You may need to configure the udev rule to have direct access.
        """
        assert transport is not None

        self.transport = transport

        self.tf = TinyFrame()
        self.tf.write = self.transport.write
        self.transport.listen(self.tf.accept)

        # test connection
        resp = self.query_raw(type=gex.MSG_PING)
        print("GEX connected, version string: %s" % resp.data.decode('utf-8'))

        # fallback error listener
        def error_lst(tf :TinyFrame, msg :TF_Msg):
            raise Exception("ERROR MESSAGE! %s" % msg.data.decode('utf-8'))
        self.tf.add_type_listener(gex.MSG_ERROR, error_lst)

        # lambda
        def unit_repot_lst(tf :TinyFrame, msg :TF_Msg):
            self.handle_unit_report(msg)
            return TF.STAY
        self.tf.add_type_listener(gex.MSG_UNIT_REPORT, unit_repot_lst)

        # fallback error listener
        def fallback_lst(tf :TinyFrame, msg :TF_Msg):
            try:
                pld_as_s = msg.data.decode('utf-8')
            except UnicodeDecodeError:
                pld_as_s = str(msg.data)
            raise Exception("UNHANDLED MESSAGE! %s" % pld_as_s)

        self.tf.add_fallback_listener(fallback_lst)

        self.unit_lu = {}
        self.report_handlers = {}

        if load_units:
            self.load_units()

    def close(self):
        self.transport.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ End of a with block, close the thread """
        self.close()

    def __enter__(self):
        """ This is needed for with blocks to work """
        return self

    def handle_unit_report(self, msg:TF_Msg):
        pp = PayloadParser(msg.data)
        callsign = pp.u8()
        event = pp.u8()
        timestamp = pp.u64()
        payload = pp.tail()

        report = EventReport(msg=msg, cs=callsign, event=event, timestamp=timestamp, payload=payload)

        if callsign in self.report_handlers:
            self.report_handlers[callsign](report)
        else:
            print("Unhandled event report: callsign %d, event %d" % (callsign, event))
            print(payload)

    def bind_report_listener(self, callsign:int, listener):
        """ Assign a report listener function to a callsign """
        self.report_handlers[callsign] = listener

    def load_units(self):
        """ Load a list of unit names and callsigns for look-up """
        resp = self.query_raw(type=gex.MSG_LIST_UNITS)
        pp = PayloadParser(resp.data)
        count = pp.u8()

        self.unit_lu = {}

        callsigns = []
        for n in range(0,count):
            cs = pp.u8()
            name = pp.str()
            type = pp.str()

            print("- Found unit \"%s\" (type %s) @ callsign %d" % (name, type, cs))
            self.unit_lu[name] = {
                'callsign': cs,
                'type': type,
            }
            if cs in callsigns:
                raise Exception("Duplicate callsign! Wrong GEX config!")
            callsigns.append(cs)

    def ini_read(self) -> str:
        """ Read the settings INI file """
        buffer = self.bulk_read(cs=None, cmd=gex.MSG_INI_READ)
        return buffer.decode('utf-8')

    def ini_write(self, buffer):
        """ Read the settings INI file """
        if type(buffer) == str:
            buffer = buffer.encode('utf-8')

        pb = gex.PayloadBuilder()
        pb.u32(len(buffer))

        self.bulk_write(cs=None, pld=pb.close(), cmd=gex.MSG_INI_WRITE, bulk=buffer)

    def ini_persist(self):
        """ Persist INI settings to Flash """
        self.send_raw(type=gex.MSG_PERSIST_SETTINGS)

    def get_callsign(self, name:str, type:str = None) -> int:
        """ Find unit by name and type """

        if name not in self.unit_lu:
            raise Exception("No %s unit called \"%s\"" % (type or '*', name))

        u = self.unit_lu[name]

        if type is not None:
            if u['type'] != type:
                raise Exception("Unit %s is not type %s (is %s)" % (name, type, u['type']))

        return u['callsign']

    def send(self, cmd:int, cs:int=None, id:int=None, pld=None, listener=None):
        """
        Send a command to a unit. If cs is None, cmd is used as message type
        Returns the ID
        """
        if cs is None:
            return self.tf.query(type=cmd, id=id, pld=pld, listener=listener)

        if pld is None:
            pld = b''

        buf = bytearray([cs, cmd])
        buf.extend(pld)
        return self.tf.query(type=gex.MSG_UNIT_REQUEST, id=id, pld=buf, listener=listener)

    def query(self, cmd:int, cs:int=None, id:int=None, pld=None) -> TF_Msg:
        """
        Query a unit. If cs is None, cmd is used as message type
        Returns the message
        """

        self._theframe = None

        def lst(tf, frame):
            self._theframe = frame
            return TF.CLOSE

        self.send(cs=cs, cmd=cmd, id=id, pld=pld, listener=lst)
        # Wait for the response (hope no unrelated frame comes in instead)

        # timeout after 3s
        self.transport.poll(3, lambda: self._theframe is not None)

        if self._theframe is None:
            raise Exception("No response to query")

        if self._theframe.type == gex.MSG_ERROR:
            raise Exception("Error response: %s" % self._theframe.data.decode('utf-8'))

        return self._theframe

    def query_async(self, cmd:int, cs:int=None, id:int=None, pld=None, callback=None):
        """
        Query a unit. If cs is None, cmd is used as message type
        Returns frame ID
        """

        assert callback is not None

        def lst(tf, frame):
            if frame.type == gex.MSG_ERROR:
                raise Exception("Error response: %s" % self._theframe.data.decode('utf-8'))

            rv = callback(frame)
            return rv if rv is not None else TF.CLOSE

        return self.send(cs=cs, cmd=cmd, id=id, pld=pld, listener=lst)

    def query_raw_async(self, type:int, id:int=None, pld=None, callback=None):
        """ Query GEX, without addressing a unit """
        assert callback is not None

        self.query_async(cs=None, cmd=type, id=id, pld=pld, callback=callback)

    def poll(self, timeout=0.1, testfunc=None):
        """
        Wait for new data or testfunc to return True
        (e.g. checking if an expected frame was received)
        """
        self.transport.poll(timeout, testfunc)

    def query_raw(self, type:int, id:int=None, pld=None) -> TF_Msg:
        """ Query GEX, without addressing a unit """
        return self.query(cs=None, cmd=type, id=id, pld=pld)

    def send_raw(self, type:int, id=None, pld=None):
        """ Send to GEX, without addressing a unit """
        return self.send(cs=None, cmd=type, id=id, pld=pld)

    def bulk_read(self, cmd:int, cs:int=None, id=None, pld=None, chunk=1024) -> bytearray:
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

    def bulk_write(self, cmd:int, bulk, cs:int=None, id:int=None, pld=None):
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
