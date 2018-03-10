import gex

CMD_WAVE_DC = 0
CMD_WAVE_SINE = 1
CMD_WAVE_TRIANGLE = 2
CMD_WAVE_SAWTOOTH_UP = 3
CMD_WAVE_SAWTOOTH_DOWN = 4
CMD_WAVE_RECTANGLE = 5

CMD_SYNC = 10

CMD_SET_FREQUENCY = 20
CMD_SET_PHASE = 21
CMD_SET_DITHER = 22

LUT_LEN = 8192

class DAC(gex.Unit):
    """
    Analog output (2 channels)
    """

    def _type(self):
        return 'DAC'


    def dc(self, channel, level, confirm=True):
        """
        Set DC levels, 0-4095. None to leave the level unchanged

        channel: 1,2 (3 = both)
        level: 0-4095
        """
        if channel != 1 and channel != 2 and channel != 3:
            raise Exception("Bad channel arg: %s" % channel)

        pb = gex.PayloadBuilder()
        pb.u8(channel)
        pb.u16(level)

        if channel==3:
            pb.u16(level)

        self._send(CMD_WAVE_DC, pld=pb.close(), confirm=confirm)


    def dc_dual(self, ch1, ch2, confirm=True):
        """
        Set DC levels, 0-4095
        """

        pb = gex.PayloadBuilder()
        pb.u8(0b11)
        pb.u16(ch1)
        pb.u16(ch2)
        self._send(CMD_WAVE_DC, pld=pb.close(), confirm=confirm)


    def rectangle(self, channel, duty=None, high=None, low=None, confirm=True):
        """ Enter rectangle gen mode (duty 0..1000) """

        if channel != 1 and channel != 2 and channel != 3:
            raise Exception("Bad channel arg: %s" % channel)

        pb = gex.PayloadBuilder()
        pb.u8(channel)  # 0b01 or 0b10

        for i in range(0,1 if channel != 3 else 2): # repeat if dual
            pb.u16(round(duty * LUT_LEN) if duty is not None # todo ??
                                         else 0xFFFF)

            pb.u16(high if high is not None else 0xFFFF)
            pb.u16(low if low is not None else 0xFFFF)

        self._send(CMD_WAVE_RECTANGLE, pld=pb.close(), confirm=confirm)


    def rectangle_dual(self,
                       duty1=None, duty2=None,
                       high1=None, high2=None,
                       low1=None, low2=None,
                       confirm=True):
        """ Set rectangle dual (both at once in sync) """

        pb = gex.PayloadBuilder()
        pb.u8(0b11)  # 0b01 or 0b10

        pb.u16(round(duty1*LUT_LEN))
        pb.u16(high1 if high1 is not None else 0xFFFF)
        pb.u16(low1 if low1 is not None else 0xFFFF)

        pb.u16(round(duty2*LUT_LEN))
        pb.u16(high2 if high2 is not None else 0xFFFF)
        pb.u16(low2 if low2 is not None else 0xFFFF)

        self._send(CMD_WAVE_RECTANGLE, pld=pb.close(), confirm=confirm)


    def sync(self, confirm=True):
        self._send(CMD_SYNC, confirm=confirm)


    def waveform(self, channel, waveform, confirm=True):
        """
        Set a waveform. For DC or rectangle,
        use the dedicated functions with extra parameters

        channel: 1,2 (3 = both)
        waveform:
        - None - leave unchanged
        - SINE
        - TRIANGLE
        - SAW_UP
        - SAW_DOWN
        """

        lookup = {'SINE': CMD_WAVE_SINE,
                  'SIN': CMD_WAVE_SINE,

                  'TRI': CMD_WAVE_TRIANGLE,
                  'TRIANGLE': CMD_WAVE_TRIANGLE,

                  'SAW': CMD_WAVE_SAWTOOTH_UP,
                  'RAMP': CMD_WAVE_SAWTOOTH_UP,
                  'RAMP_UP': CMD_WAVE_SAWTOOTH_UP,
                  'SAW_UP': CMD_WAVE_SAWTOOTH_UP,

                  'SAW_DOWN': CMD_WAVE_SAWTOOTH_DOWN,
                  'RAMP_DOWN': CMD_WAVE_SAWTOOTH_DOWN,
                  }

        if channel != 1 and channel != 2 and channel != 3:
            raise Exception("Bad channel arg: %s" % channel)

        pb = gex.PayloadBuilder()
        pb.u8(channel) # 0b01 or 0b10
        self._send(lookup[waveform], pld=pb.close(), confirm=confirm)


    def set_frequency(self, channel, freq, confirm=True):
        """
        Set frequency using float in Hz
        """

        if channel != 1 and channel != 2 and channel != 3:
            raise Exception("Bad channel arg: %s" % channel)

        pb = gex.PayloadBuilder()
        pb.u8(channel)
        pb.float(freq)

        if channel == 3:
            pb.float(freq)

        self._send(CMD_SET_FREQUENCY, pld=pb.close(), confirm=confirm)


    def set_frequency_dual(self, freq1, freq2, confirm=True):
        """
        Set frequency of both channels using float in Hz
        """

        pb = gex.PayloadBuilder()
        pb.u8(0b11)
        pb.float(freq1)
        pb.float(freq2)

        self._send(CMD_SET_FREQUENCY, pld=pb.close(), confirm=confirm)


    def set_phase(self, channel, phase360, confirm=True):
        """
        Set channel phase relative to it's "base phase".
        If both channels use the same frequency, this could be used for drawing XY figures.
        """

        if channel != 1 and channel != 2 and channel != 3:
            raise Exception("Bad channel arg: %s" % channel)

        pb = gex.PayloadBuilder()
        pb.u8(channel)
        pb.u16(round((phase360/360) * LUT_LEN))

        if channel == 3:
            pb.u16(round((phase360/360) * LUT_LEN))

        self._send(CMD_SET_PHASE, pld=pb.close(), confirm=confirm)


    def set_phase_dual(self, phase1, phase2, confirm=True):
        """
        Set phase for both channels at once
        """

        pb = gex.PayloadBuilder()
        pb.u8(0b11)
        pb.u16((phase1/360) * LUT_LEN)
        pb.u16((phase2/360) * LUT_LEN)

        self._send(CMD_SET_PHASE, pld=pb.close(), confirm=confirm)


    def set_dither(self, channel, type=None, bits=None, confirm=True):
        """
        Set dithering (superimposed noise waveform)
        type: NONE, TRIANGLE, WHITE
        bits: 1-12
        """

        if channel != 1 and channel != 2 and channel != 3:
            raise Exception("Bad channel arg: %s" % channel)

        lookup = {'NONE': 0,

                  'WHITE': 1,
                  'NOISE': 1,

                  'TRIANGLE': 2,
                  'TRI': 2}

        pb = gex.PayloadBuilder()
        pb.u8(channel)

        for i in range(0,1 if channel != 3 else 2): # repeat if dual
            pb.u8(lookup[type] if type is not None else 0xFF)
            pb.u8(bits if bits is not None else 0xFF)

        self._send(CMD_SET_DITHER, pld=pb.close(), confirm=confirm)
