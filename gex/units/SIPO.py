import gex

CMD_WRITE = 0
CMD_DIRECT_DATA = 1
CMD_DIRECT_SHIFT = 2
CMD_DIRECT_CLEAR = 3
CMD_DIRECT_STORE = 4

class SIPO(gex.Unit):
    """
    Multi-channel SIPO driver
    Designed for loading up to 16 74xx595 or 74xx4094 serial-input-parallel-output shift registers
    The number of drivers can be significantly expanded via daisy-chaining.
    """

    def _type(self):
        return 'SIPO'

    def load(self, buffers, confirm=True):
        """ Load data - buffers is a list of lists or byte arrays """
        if type(buffers[0]) == int:
            buffers = [buffers]

        pb = gex.PayloadBuilder()
        for b in buffers:
            pb.blob(b)

        self._send(CMD_WRITE, pb.close(), confirm=confirm)

    def set_data(self, packed:int, confirm=True):
        """ Manually set the data pins """
        pb = gex.PayloadBuilder()
        pb.u16(packed)
        self._send(CMD_DIRECT_DATA, pb.close(), confirm=confirm)

    def shift(self, confirm=True):
        """ Manually send a shift pulse (shift data one step further into the registers)  """
        self._send(CMD_DIRECT_SHIFT, confirm=confirm)

    def store(self, confirm=True):
        """ Manually send a store pulse (copy the shift register data to the outputs) """
        self._send(CMD_DIRECT_STORE, confirm=confirm)

    def clear(self, confirm=True):
        """ Manually send a clear pulse (if connected correctly, this immediately resets the shift register outputs) """
        self._send(CMD_DIRECT_CLEAR, confirm=confirm)
