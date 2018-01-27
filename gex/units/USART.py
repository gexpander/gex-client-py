import gex

class USART(gex.Unit):
    """
    USART
    """

    def _type(self):
        return 'USART'

    def listen(self, handler, decode='utf-8'):
        """
        Attach a Rx listener callback.
        decode can be: None, 'utf-8', 'ascii' (any valid encoding for bytearray.decode())
        None decoding returns bytearray

        handler receives args: (bytes, timestamp)
        """
        self.handler_decode = decode
        self.handler = handler

    def write(self, payload, sync=False, confirm=True):
        """
        Write bytes. If 'sync' is True, wait for completion. sync implies confirm
        """

        if type(payload) is str:
            payload = payload.encode('utf-8')

        pb = gex.PayloadBuilder()
        pb.blob(payload) # payload to write

        self._send(0x01 if sync else 0x00, pb.close(), confirm=confirm or sync)

    def _on_event(self, event:int, payload, timestamp:int):
        if event == 0:
            # Data received
            if self.handler:
                data = payload if self.handler_decode is None \
                               else payload.decode(self.handler_decode)

                self.handler(data, timestamp)
