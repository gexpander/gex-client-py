import gex

CMD_SET_FREQUENCY = 0
CMD_SET_DUTY = 1
CMD_STOP = 2
CMD_START = 3

class PWMDim(gex.Unit):
    """
    Simple 4-channel PWM output with a common frequency
    """

    def _type(self):
        return 'PWMDIM'

    def set_frequency(self, hertz:int, confirm=True):
        """ Set freq """
        pb = gex.PayloadBuilder()
        pb.u32(hertz)
        self._send(CMD_SET_FREQUENCY, pb.close(), confirm=confirm)

    def set_duty(self, duty_dict, confirm=True):
        """ Set duty (dict - number1234 -> duty 0-1000) """
        pb = gex.PayloadBuilder()

        for (k,v) in enumerate(duty_dict):
            pb.u8(k-1)
            pb.u16(v)

        self._send(CMD_SET_DUTY, pb.close(), confirm=confirm)

    def set_duty_single(self, ch1234, duty1000, confirm=True):
        """ Set duty of a single channel """
        pb = gex.PayloadBuilder()
        pb.u8(ch1234-1)
        pb.u16(duty1000)
        self._send(CMD_SET_DUTY, pb.close(), confirm=confirm)

    def stop(self, confirm=True):
        self._send(CMD_STOP, confirm=confirm)

    def start(self, confirm=True):
        self._send(CMD_START, confirm=confirm)
