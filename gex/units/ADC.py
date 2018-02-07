import gex
from gex import TF, TF_Msg
from gex.Client import EventReport

CMD_READ_RAW = 0
CMD_READ_SMOOTHED = 1
CMD_GET_ENABLED_CHANNELS = 10
CMD_SETUP_TRIGGER = 20
CMD_ARM = 21
CMD_DISARM = 22
CMD_ABORT = 23
CMD_FORCE_TRIGGER = 24
CMD_BLOCK_CAPTURE = 25
CMD_STREAM_START = 26
CMD_STREAM_STOP = 27
CMD_SET_SMOOTHING_FACTOR = 28

EVT_CAPT_START = 0
EVT_CAPT_MORE = 1
EVT_CAPT_DONE = 2

EVT_STREAM_START = 10
EVT_STREAM_DATA = 11
EVT_STREAM_END = 12

class TriggerReport:
    def __init__(self, buf, edge, pretrig, timestamp):
        self.buf = buf
        self.edge = edge
        self.pretrig = pretrig
        self.timestamp = timestamp

class ADC(gex.Unit):
    """
    ADC device
    """

    def _type(self):
        return 'ADC'

    def _init(self):
        self._trig_buf = None
        self._trig_edge = 0 # 1, 2, 3
        self._trig_pretrig_len = 0
        self._trig_next_id = 0
        self._trig_listener = None
        self._trig_ts = 0

        self._stream_next_id = 0
        self._stream_running = False
        self._stream_listener = None

    def _on_trig_capt(self, msg:TF_Msg):
        print("Capture")
        pp = gex.PayloadParser(msg.data)

        if self._trig_buf is None:
            raise Exception("Unexpected capture data frame")

        # All but the first trig capture frame are prefixed by a sequence number
        if self._trig_next_id != 0:
            idx = pp.u8()
            if idx != self._trig_next_id:
                raise Exception("Lost capture data frame! Expected %d, got %d" % (self._bcap_next_id, idx))
        self._trig_next_id = (self._trig_next_id + 1) % 256

        self._trig_buf.extend(pp.tail())

        if msg.type == EVT_CAPT_DONE:
            if self._trig_listener is not None:
                self._trig_listener(TriggerReport(buf=self._trig_buf,
                                                  edge=self._trig_edge,
                                                  pretrig=self._trig_pretrig_len,
                                                  timestamp=self._trig_ts))

            self._trig_buf = None
            # We keep the trig listener
            return TF.CLOSE
        else:
            return TF.STAY

    def _on_stream_capt(self, msg:TF_Msg):
        print("Stream data frame")
        pp = gex.PayloadParser(msg.data)

        if not self._stream_running:
            raise Exception("Unexpected stream data frame")

        if msg.type == EVT_STREAM_END:
            if self._stream_listener is not None:
                self._stream_listener(None) # Indicate it's closed

            # We keep the stream listener, so user doesnt have to set it before each stream
            self._stream_running = False
            return TF.CLOSE
        else:
            # All stream data frames are prefixed by a sequence number
            idx = pp.u8()
            if idx != self._stream_next_id:
                self._stream_running = False
                raise Exception("Lost stream data frame! Expected %d, got %d" % (self._bcap_next_id, idx))

            self._stream_next_id = (self._stream_next_id + 1) % 256

            tail = pp.tail()

            if self._stream_listener is not None:
                self._stream_listener(tail)

            return TF.STAY

    def _on_event(self, evt:EventReport):
        """
        Handle a trigger or stream start event.

        - EVT_CAPT_START
          First frame payload: edge:u8, pretrig_len:u16, payload:tail

          Following are plain TF frames with the same ID, each prefixed with a sequence number in 1 byte.
          Type EVT_CAPT_MORE or EVT_CAPT_DONE indicate whether this is the last frame of the sequence,
          after which the ID listener should be removed.

        - EVT_STREAM_START
          regular GEX event format, payload is the first data block, INCLUDING a numeric prefix (0) - 1 byte
          Following frames are plain TF frames with type EVT_STREAM_DATA or EVT_STREAM_END, also including the incrementing prefix.

        """
        print("ADC event %d" % evt.code)

        pp = gex.PayloadParser(evt.payload)
        msg = evt.msg

        if evt.code == EVT_CAPT_START:
            if self._trig_buf is not None:
                raise Exception("Unexpected start of capture")

            self._trig_ts = evt.timestamp
            self._trig_buf = bytearray()
            self._trig_edge = pp.u8()
            self._trig_pretrig_len = pp.u16()
            self._trig_next_id = 0
            msg.data = pp.tail()
            self._on_trig_capt(msg)
            self.client.tf.add_id_listener(msg.id, lambda tf,msg: self._on_trig_capt(msg))

    def get_channels(self):
        """
        Find enabled channel numbers.
        Returns a list.
        """
        msg = self._query(CMD_GET_ENABLED_CHANNELS)
        return list(msg.data)

    def set_smoothing_factor(self, fac, confirm=True):
        """ Set smoothing factor for read_smooth(), range 0-1.0 """
        pb = gex.PayloadBuilder()
        pb.u16(round(fac*1000))
        self._send(CMD_SET_SMOOTHING_FACTOR, pld=pb.close(), confirm=confirm)

    def read_raw(self):
        """ Read raw values. Returns a dict. """
        msg = self._query(CMD_READ_RAW)
        pp = gex.PayloadParser(msg)
        chs = dict()
        while pp.length() > 0:
            idx = pp.u8()
            chs[idx] = pp.u16()
        return chs

    def read_smooth(self):
        """ Read smoothed values (floats). Returns a dict. """
        msg = self._query(CMD_READ_SMOOTHED)
        pp = gex.PayloadParser(msg)
        chs = dict()
        while pp.length() > 0:
            idx = pp.u8()
            chs[idx] = pp.float()
        return chs

    def on_trigger(self, lst):
        """ Set the trigger handler """
        self._trig_listener = lst

    def off_trigger(self):
        """ Remove the trigger handler """
        self.on_trigger(None)

    def setup_trigger(self, channel, level, count, edge='rising', pretrigger=0, holdoff=100, auto=False, confirm=True, handler=None):
        """
        Configure a trigger.

        channel - 0-17 (16-tsense, 17-vrefint)
        level   - triggering threshold, raw (0-4095)
        count   - nbr of samples to capture after trigger
        edge    - "rising", "falling" or "both"
        pretrigger - nbr of samples to capture before the trigger occurred. Limited by the internal buffer.
        holdoff - hold-off time (trigger also can't fire while the capture is ongoing, and if it's not armed)
        auto    - auto re-arm after completing the capture. Normally the state switches to IDLE.
        handler - attaches a callback handler for the received data
        """

        nedge = 0
        if edge == 'rising':
            nedge = 1
        elif edge == 'falling':
            nedge = 2
        elif edge == 'both':
            nedge = 3
        else:
            raise Exception("Bad edge arg")

        pb = gex.PayloadBuilder()
        pb.u8(channel)
        pb.u16(level)
        pb.u8(nedge)
        pb.u16(pretrigger)
        pb.u32(count)
        pb.u16(holdoff)
        pb.bool(auto)

        self._send(cmd=CMD_SETUP_TRIGGER, pld=pb.close(), confirm=confirm)

        if handler is not None:
            self._trig_listener = handler

    def arm(self, auto=None, confirm=True):
        """
        ARM for trigger.
        The trigger must be configured first.

        if auto is True or False, it sets the auto-rearm flag.
        """

        pb = gex.PayloadBuilder()

        if auto is None:
            pb.u8(255)
        else:
            pb.u8(1 if auto else 0)

        self._send(cmd=CMD_ARM, pld=pb.close(), confirm=confirm)

    def disarm(self, confirm=True):
        """
        DISARM.
        No effect if not armed.
        Always clears the auto-arm flag.
        """
        self._send(cmd=CMD_DISARM, confirm=confirm)

    def abort(self, confirm=True):
        """
        Abort any ongoing capture and dis-arm.
        Also clears the auto-arm flag.
        """
        self._send(cmd=CMD_ABORT, confirm=confirm)

    def force(self, handler=None, confirm=True):
        """
        Force a trigger, including pre-trigger capture.
        The device behavior is identical as if the trigger condition occurred naturally.

        The captured data is received asynchronously via an event.
        """
        if handler is not None:
            self.on_trigger(handler)

        self._send(cmd=CMD_FORCE_TRIGGER, confirm=confirm)

    def capture_in_progress(self):
        return self._stream_running or self._trig_buf is not None

    def capture(self, count, timeout=5):
        """
        Start a block capture.
        This is similar to a forced trigger, but has custom size and doesn't include any pre-trigger.

        The captured data is received synchronously and returned.
        """

        if self.capture_in_progress():
            raise Exception("Another capture already in progress")

        pb = gex.PayloadBuilder()
        pb.u32(count)

        buffer = bytearray()
        self._bcap_next_id = 0
        self._bcap_done = False
        self._stream_running = True # we use this flag to block any concurrent access

        def lst(frame):
            pp = gex.PayloadParser(frame.data)

            index = pp.u8()
            if index != self._bcap_next_id:
                self._bcap_done = True
                raise Exception("Lost capture data frame! Expected %d, got %d" % (self._bcap_next_id, index))
                #return TF.CLOSE XXX

            self._bcap_next_id = (self._bcap_next_id + 1) % 256

            buffer.extend(pp.tail())

            if frame.type == EVT_CAPT_DONE:
                self._bcap_done = True
                return TF.CLOSE
            return TF.STAY

        self._query_async(cmd=CMD_BLOCK_CAPTURE, pld=pb.close(), callback=lst)

        # wait with a timeout
        self.client.transport.poll(timeout, lambda: self._bcap_done == True)

        self._stream_running = False

        if not self._bcap_done:
            raise Exception("Capture not completed within timeout")

        return buffer

    def on_stream(self, lst):
        self._stream_listener = lst

    def off_stream(self, lst):
        self.on_stream(None)

    def stream_start(self, lst=None):
        """ Start a capture stream """
        if self.capture_in_progress():
            raise Exception("Another capture already in progress")

        self._stream_next_id = 0
        self._stream_running = True

        if lst is not None:
            self._stream_listener = lst

        def str_lst(tf, msg):
            self._on_stream_capt(msg)

        self._query_async(cmd=CMD_STREAM_START, callback=str_lst)

    def stream_stop(self, lst, confirm=True):
        """ Stop a stream """
        if not self._stream_running:
            raise Exception("Not streaming")

        self._stream_listener = None
        self._send(cmd=CMD_STREAM_STOP, confirm=confirm)
