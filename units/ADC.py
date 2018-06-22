import array

import time

import gex
from gex import TF, TF_Msg
from gex.Client import EventReport

import numpy as np

CMD_READ_RAW = 0
CMD_READ_SMOOTHED = 1
CMD_READ_CAL_CONSTANTS = 2
CMD_GET_ENABLED_CHANNELS = 10
CMD_GET_SAMPLE_RATE = 11

CMD_SETUP_TRIGGER = 20
CMD_ARM = 21
CMD_DISARM = 22
CMD_ABORT = 23
CMD_FORCE_TRIGGER = 24
CMD_BLOCK_CAPTURE = 25
CMD_STREAM_START = 26
CMD_STREAM_STOP = 27
CMD_SET_SMOOTHING_FACTOR = 28
CMD_SET_SAMPLE_RATE = 29
CMD_ENABLE_CHANNELS = 30
CMD_SET_SAMPLE_TIME = 31

EVT_CAPT_START = 50
EVT_CAPT_MORE = 51
EVT_CAPT_DONE = 52

class TriggerReport:
    def __init__(self, data, edge, pretrig, timestamp):
        self.data = data
        self.edge = edge
        self.pretrig = pretrig
        self.timestamp = timestamp

    def __str__(self):
        return "EventReport(edge %d, pretrig len %d, ts %d, data %s)" % (self.edge, self.pretrig, self.timestamp, self.data)

class ADC_CalData:
    def __init__(self, pp:gex.PayloadParser):
        self.VREFINT_CAL = pp.u16() # ADC raw value for VREFINT, 30C ambient
        self.VREFINT_CAL_VADCREF = pp.u16() # Analog reference voltage during VREFINT calibration (mV) +-10mV

        self.TSENSE_CAL1 = pp.u16() # ADC raw value in point 1
        self.TSENSE_CAL2 = pp.u16() # ADC raw value in point 2
        self.TSENSE_CAL1_TEMP = pp.u8() # Temperature for point 1 (Celsius) +-5C
        self.TSENSE_CAL2_TEMP = pp.u8() # Temperature for point 2 (Celsius) +-5C
        self.TSENSE_CAL_VADCREF = pp.u16() # Analog reference voltage during TSENSE calibration (mV) +-10mV

    def __str__(self):
        return "ADC_CalData(VREFINT=%d at Vref=%d mV, TSENSE_%dC=%d, TSENSE_%dC=%d at Vref=%d mV)" % \
               (self.VREFINT_CAL, self.VREFINT_CAL_VADCREF,
                self.TSENSE_CAL1_TEMP, self.TSENSE_CAL1, self.TSENSE_CAL2_TEMP, self.TSENSE_CAL2, self.TSENSE_CAL_VADCREF)

    # TODO utility for converting raw values to real voltage / temperature

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

        self.channels = self.get_channels()
        (_, self.sample_rate) = self.get_sample_rate()

    def _on_trig_capt(self, msg:TF_Msg):
        pp = gex.PayloadParser(msg.data)

        if self._trig_buf is None:
            raise Exception("Unexpected capture data frame")

        # All but the first trig capture frame are prefixed by a sequence number

        idx = pp.u8()
        if idx != self._trig_next_id:
            raise Exception("Lost capture data frame! Expected %d, got %d" % (self._trig_next_id, idx))
        self._trig_next_id = (self._trig_next_id + 1) % 256

        self._trig_buf.extend(pp.tail())

        if msg.type == EVT_CAPT_DONE:
            if self._trig_listener is not None:
                self._trig_listener(TriggerReport(data=self._parse_buffer(self._trig_buf),
                                                  edge=self._trig_edge,
                                                  pretrig=self._trig_pretrig_len,
                                                  timestamp=self._trig_ts))

            self._trig_buf = None
            # We keep the trig listener
            return TF.CLOSE
        else:
            return TF.STAY

    def _on_stream_capt(self, msg:TF_Msg):
        pp = gex.PayloadParser(msg.data)

        if not self._stream_running:
            raise Exception("Unexpected stream data frame")

        if msg.type == EVT_CAPT_DONE:
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
                raise Exception("Lost stream data frame! Expected %d, got %d" % (self._stream_next_id, idx))

            self._stream_next_id = (self._stream_next_id + 1) % 256

            tail = pp.tail()

            if self._stream_listener is not None:
                self._stream_listener(self._parse_buffer(tail))

            return TF.STAY

    def _on_event(self, evt:EventReport):
        """
        Handle a trigger or stream start event.

        - EVT_CAPT_START
          First frame payload: edge:u8, pretrig_len:u32, payload:tail

          Following are plain TF frames with the same ID, each prefixed with a sequence number in 1 byte.
          Type EVT_CAPT_MORE or EVT_CAPT_DONE indicate whether this is the last frame of the sequence,
          after which the ID listener should be removed.

        """
        pp = gex.PayloadParser(evt.payload)
        msg = evt.msg

        if evt.code == EVT_CAPT_START:
            if self._trig_buf is not None:
                raise Exception("Unexpected start of capture")

            self._trig_ts = evt.timestamp
            self._trig_buf = bytearray()

            self._trig_pretrig_len = pp.u32()

            self._trig_edge = pp.u8()

            self._trig_next_id = 0
            msg.data = pp.tail()

            # the rest is a regular capture frame with seq
            self._on_trig_capt(msg)
            self.client.tf.add_id_listener(msg.id, lambda tf,msg: self._on_trig_capt(msg))

    def get_channels(self):
        """
        Find enabled channel numbers.
        Returns a list.
        """
        msg = self._query(CMD_GET_ENABLED_CHANNELS)
        return list(msg.data)

    def get_calibration_data(self):
        """
        Read ADC calibration data
        """
        msg = self._query(CMD_READ_CAL_CONSTANTS)
        return ADC_CalData(gex.PayloadParser(msg.data))

    def set_sample_rate(self, freq:int):
        """ Set sample rate in Hz. Returns the real achieved frequency as float. """
        pb = gex.PayloadBuilder()
        pb.u32(freq)
        msg = self._query(CMD_SET_SAMPLE_RATE, pld=pb.close())
        pp = gex.PayloadParser(msg.data)

        req = pp.u32()
        real = pp.float()

        self.sample_rate = real

        return real

    def set_sample_time(self, sample_time:int, confirm=True):
        """ Set sample time. Values 0-7 """
        pb = gex.PayloadBuilder()
        pb.u8(sample_time)
        self._send(CMD_SET_SAMPLE_TIME, pld=pb.close(), confirm=confirm)

    def get_sample_rate(self):
        """
        Get the current real sample rate as float.
        Returns tuple (requested:int, real:float)
        """
        msg = self._query(CMD_GET_SAMPLE_RATE)
        pp = gex.PayloadParser(msg.data)

        req = pp.u32()
        real = pp.float()

        return (req, real)

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
        i = 0
        while pp.length() > 0:
            chs[self.channels[i]] = pp.u16()
            i += 1
        return chs

    def read_smooth(self):
        """ Read smoothed values (floats). Returns a dict. """
        msg = self._query(CMD_READ_SMOOTHED)
        pp = gex.PayloadParser(msg)
        chs = dict()
        i = 0
        while pp.length() > 0:
            chs[self.channels[i]] = pp.float()
            i += 1
        return chs

    def on_trigger(self, lst):
        """ Set the trigger handler """
        self._trig_listener = lst

    def off_trigger(self):
        """ Remove the trigger handler """
        self.on_trigger(None)

    def setup_trigger(self, channel, level, count,
                      edge='rising', pretrigger=0, holdoff=100,
                      auto=False, confirm=True, handler=None):
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
        if edge == 'rising' or edge == 'up':
            nedge = 1
        elif edge == 'falling' or edge == 'down':
            nedge = 2
        elif edge == 'both':
            nedge = 3
        else:
            raise Exception("Bad edge arg")

        pb = gex.PayloadBuilder()
        pb.u8(channel)
        pb.u16(level)
        pb.u8(nedge)
        pb.u32(pretrigger)
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

    def set_active_channels(self, channels, confirm=True):
        """
        Set which channels should be active.
        """

        pb = gex.PayloadBuilder()
        pb.u32(self.pins2int(channels))

        self._send(cmd=CMD_ENABLE_CHANNELS, pld=pb.close(), confirm=confirm)
        self.channels = self.pins2list(channels)

    def _parse_buffer(self, buf):
        """
        Convert a raw buffer to a more useful format
        """
        arr = np.array(array.array('h', buf))
        return np.reshape(arr, (-1,len(self.channels)))

    def capture_in_progress(self):
        return self._stream_running or self._trig_buf is not None

    def capture(self, count, timeout=None, async=False, lst=None):
        """
        Start a block capture.
        This is similar to a forced trigger, but has custom size and doesn't include any pre-trigger.

        The captured data is received synchronously and returned as a dict of channel arrays
        """

        if self.capture_in_progress():
            raise Exception("Another capture already in progress")

        if timeout is None:
            timeout = 1 + float(count)/self.sample_rate * 2
            #print("Timeout = %f" % timeout)

        pb = gex.PayloadBuilder()
        pb.u32(count)

        buffer = bytearray()
        self._bcap_next_id = 0
        self._bcap_done = False
        self._stream_running = True # we use this flag to block any concurrent access

        def _lst(frame):
            pp = gex.PayloadParser(frame.data)

            if frame.type == EVT_CAPT_MORE or len(frame.data) != 0:
                index = pp.u8()
                if index != self._bcap_next_id:
                    self._bcap_done = True
                    raise Exception("Lost capture data frame! Expected %d, got %d" % (self._bcap_next_id, index))
                    #return TF.CLOSE XXX

                self._bcap_next_id = (self._bcap_next_id + 1) % 256

                buffer.extend(pp.tail())

            if frame.type == EVT_CAPT_DONE:
                self._bcap_done = True
                if async:
                    lst(self._parse_buffer(buffer))
                    self._stream_running = False
                return TF.CLOSE

            return TF.STAY

        self._query_async(cmd=CMD_BLOCK_CAPTURE, pld=pb.close(), callback=_lst)

        if not async:
            # wait with a timeout
            self.client.transport.poll(timeout, lambda: self._bcap_done == True)

            self._stream_running = False

            if not self._bcap_done:
                self.abort()
                raise Exception("Capture not completed within timeout")

            return self._parse_buffer(buffer)

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

        self._query_async(cmd=CMD_STREAM_START, callback=self._on_stream_capt)

    def stream_stop(self, delay=0.1, confirm=True):
        """
        Stop a stream. Delay is an extra time before removing the listener
        to let the queued frames to finish being received.
        """
        if not self._stream_running:
            raise Exception("Not streaming")

        self._send(cmd=CMD_STREAM_STOP, confirm=confirm)
        time.sleep(delay)
        self._stream_listener = None
