import gex

CMD_STOP = 0

# Measuring a waveform
CMD_INDIRECT_CONT_START = 1  # keep measuring, read on demand
CMD_INDIRECT_BURST_START = 2 # wait and reply

# Counting pulses
CMD_DIRECT_CONT_START = 3  # keep measuring, read on demand
CMD_DIRECT_BURST_START = 4 # wait and reply
CMD_FREECOUNT_START = 5    # keep counting pulses until stopped, read on reply

CMD_MEASURE_SINGLE_PULSE = 6
CMD_FREECOUNT_CLEAR = 7

# Results readout for continuous modes
CMD_INDIRECT_CONT_READ = 10
CMD_DIRECT_CONT_READ = 11
CMD_FREECOUNT_READ = 12

CMD_SET_POLARITY = 20
CMD_SET_DIR_PRESC = 21
CMD_SET_INPUT_FILTER = 22
CMD_SET_DIR_MSEC = 23

CMD_RESTORE_DEFAULTS = 30


class FCAP_Report:
    def __init__(self):
        self.period = None # s
        self.ontime = None # s
        self.frequency = None # Hz
        self.duty = None # [-]

        # Raw data (can be used to avoid distortion by float arithmetics)
        self.period_raw = None
        self.ontime_raw = None
        self.sample_count = None
        self.clock_freq = None # Hz
        self.meas_time_ms = None

    def __str__(self):
        s = "{\n"
        if self.frequency is not None:
            s += " f = %f Hz\n" % self.frequency
        if self.period is not None:
            s += " T = %f s\n" % self.period
        if self.ontime is not None:
            s += " Ton = %f s\n" % self.ontime
        if self.duty is not None:
            s += " duty = %f\n" % self.duty
        s += "}"

        return s

class FCAP(gex.Unit):
    """
    Frequency and pulse measurement
    """

    def _type(self):
        return 'FCAP'

    def stop(self, confirm=True):
        """ Stop any ongoing capture """
        self._send(CMD_STOP, confirm=confirm)

    def configure(self,
                  polarity=None,
                  presc=None,
                  filter=None,
                  msec=None,
                  confirm=True):
        """
        Re-configure some capture parameters. None = unchanged

        polarity:  0,1  active level
        presc: 1,2,4,8  pulse counter prescaller
        filter:   0-15  digital input filter
        msec:   <65535  milliseconds for direct capture
        """

        if polarity is not None:
            pb = gex.PayloadBuilder()
            pb.u8(polarity) # 0,1
            self._send(CMD_SET_POLARITY, pld=pb.close(), confirm=confirm)

        if presc is not None:
            pb = gex.PayloadBuilder()
            pb.u8(presc)
            self._send(CMD_SET_DIR_PRESC, pld=pb.close(), confirm=confirm)

        if filter is not None:
            pb = gex.PayloadBuilder()
            pb.u8(filter)
            self._send(CMD_SET_INPUT_FILTER, pld=pb.close(), confirm=confirm)

        if msec is not None:
            pb = gex.PayloadBuilder()
            pb.u16(msec)
            self._send(CMD_SET_DIR_MSEC, pld=pb.close(), confirm=confirm)

    def config_reset(self, confirm=True):
        """ Reset all config to persistent defaults and switch to IDLE mode. """
        self._send(CMD_RESTORE_DEFAULTS, confirm=confirm)

    def indirect_start(self, confirm=True):
        """ Start continuous PWM measurement """
        self._send(CMD_INDIRECT_CONT_START, confirm=confirm)

    def counter_start(self, presc=None, confirm=True):
        """ Start the free-running counter """

        pb = gex.PayloadBuilder()
        pb.u8(presc or 0)
        self._send(CMD_FREECOUNT_START, pld=pb.close(), confirm=confirm)

    def counter_read(self):
        """ Read the free counter value """

        resp = self._query(CMD_FREECOUNT_READ)
        pp = gex.PayloadParser(resp.data)
        return pp.u32()

    def counter_clear(self):
        """
        Restart the free-running counter, returns current value before the clear.
        This should lose at most 1 tick for signals where f < core clock speed
        """

        resp = self._query(CMD_FREECOUNT_CLEAR)
        pp = gex.PayloadParser(resp.data)
        return pp.u32()

    def direct_start(self, msec=None, presc=None, confirm=True):
        """
        Start continuous PWM measurement

        msec - measurement time (ms), <65535
        presc - pre-divider, 1,2,4,8.

        arg None = unchanged
        """

        pb = gex.PayloadBuilder()
        pb.u16(msec or 0)
        pb.u8(presc or 0)
        self._send(CMD_DIRECT_CONT_START, pld=pb.close(), confirm=confirm)

    def indirect_read(self):
        """
        Read the current indirect continuous measurement values
        Returns value of the last measurement in continuous indirect mode
        """

        resp = self._query(CMD_INDIRECT_CONT_READ)
        pp = gex.PayloadParser(resp.data)

        mhz = pp.u16()
        period = pp.u32()
        ontime = pp.u32()

        rp = FCAP_Report()
        rp.period = period / (mhz*1e6) # to seconds
        rp.frequency = 1 / rp.period
        rp.ontime = ontime / (mhz*1e6) # in seconds
        rp.duty = rp.ontime / rp.period

        rp.clock_freq = mhz*1e6
        rp.sample_count = 1
        rp.period_raw = period
        rp.ontime_raw = ontime

        # returned in microseconds
        return rp

    def _process_direct_resp(self, resp):
        pp = gex.PayloadParser(resp.data)

        presc = pp.u8()
        msec = pp.u16()
        count = pp.u32() * presc

        rp = FCAP_Report()

        if count > 0:
            sec = msec / 1000
            freq = count / sec
            period = 1 / freq

            rp.period = period
            rp.frequency = freq

        rp.sample_count = count * presc
        rp.meas_time_ms = msec

        return rp

    def direct_read(self):
        """
        Read the current direct continuous measurement values
        Returns value of the last measurement in continuous direct mode
        """

        resp = self._query(CMD_DIRECT_CONT_READ)
        return self._process_direct_resp(resp)

    def measure_pulse(self, polarity=None, timeout=5):
        """
        Measure a pulse. Optionally set polarity
        """

        if polarity is not None:
            self.configure(polarity=polarity)

        resp = self._query(CMD_MEASURE_SINGLE_PULSE, timeout=timeout)
        pp = gex.PayloadParser(resp.data)

        mhz = pp.u16()
        ontime = pp.u32()

        rp = FCAP_Report()
        rp.ontime = ontime / (mhz * 1e6)  # in seconds

        rp.clock_freq = mhz * 1e6
        rp.sample_count = 1
        rp.ontime_raw = ontime

        return rp

    def indirect_burst(self, count, timeout=5):
        """
        Perform a burst measure with averaging (sum/count)
        """

        pb = gex.PayloadBuilder()
        pb.u16(count)

        resp = self._query(CMD_INDIRECT_BURST_START, pld=pb.close(), timeout=timeout)
        pp = gex.PayloadParser(resp.data)

        mhz = pp.u16()
        nsamp = pp.u16()
        period = pp.u64()
        ontime = pp.u64()

        rp = FCAP_Report()
        rp.period = period / (nsamp*mhz*1e6) # to seconds
        rp.frequency = 1 / rp.period
        rp.ontime = ontime / (nsamp*mhz*1e6) # in seconds
        rp.duty = rp.ontime / rp.period

        rp.clock_freq = mhz*1e6
        rp.sample_count = 1
        rp.period_raw = period
        rp.ontime_raw = ontime

        return rp

    def direct_burst(self, msec=1000, presc=None):
        """
        Perform direct burst measurement
        """

        pb = gex.PayloadBuilder()
        pb.u16(msec)
        pb.u8(presc or 0)

        resp = self._query(CMD_DIRECT_BURST_START,
                           pld=pb.close(),
                           timeout=(msec/1000)+1)
        return self._process_direct_resp(resp)
