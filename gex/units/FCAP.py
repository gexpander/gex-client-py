import gex

CMD_STOP = 0
CMD_PWM_CONT_START = 1
CMD_PWM_BURST_START = 2
CMD_PWM_CONT_READ = 10

class FCAP_Report:
    def __init__(self):
        self.period = 0
        self.ontime = 0
        self.frequency = 0
        self.duty = 0

        # Raw data (can be used to avoid distortion by float arithmetics)
        self.period_raw = 0
        self.ontime_raw = 0
        self.sample_count = 0
        self.clock_freq = 0

    def __str__(self):
        return "{\n f = %f Hz\n T = %f s\n Ton = %f s\n duty = %f\n}" % \
               (self.frequency, self.period, self.ontime, self.duty)

class FCAP(gex.Unit):
    """
    Frequency and pulse measurement
    """

    def _type(self):
        return 'FCAP'

    def stop(self, confirm=True):
        """ Stop any ongoing capture """
        self._send(CMD_STOP, confirm=confirm)

    def indirect_start(self, confirm=True):
        """ Start continuous PWM measurement """
        self._send(CMD_PWM_CONT_START, confirm=confirm)

    def indirect_read(self):
        """
        Read the current continuous measurement values
        Returns value of the last measurement in continuous mode
        """

        resp = self._query(CMD_PWM_CONT_READ)
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

    def indirect_single(self, timeout=5):
        """
        Perform a burst measure with averaging (sum/count)
        """
        return self.indirect_burst(count=1, timeout=timeout)

    def indirect_burst(self, count, timeout=5):
        """
        Perform a burst measure with averaging (sum/count)
        """

        pb = gex.PayloadBuilder()
        pb.u16(count)

        resp = self._query(CMD_PWM_BURST_START, pld=pb.close(), timeout=timeout)
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

