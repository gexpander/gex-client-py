import threading

import gex
from gex.Client import EventReport


class USART(gex.Unit):
    """
    USART
    """

    def _init(self):
        self.handler_decode = None
        self.handler = None
        self.buffer = bytearray()
        self.rxwaitnum = 0
        self.rxdoneSem = threading.Semaphore()

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

    def _on_event(self, evt:EventReport):
        if evt.code == 0:
            # Data received
            if self.handler:
                data = evt.payload if self.handler_decode is None \
                               else evt.payload.decode(self.handler_decode)

                self.handler(data, evt.timestamp)
            else:
                self.buffer.extend(evt.payload)
                if len(self.buffer) >= self.rxwaitnum:
                    self.rxdoneSem.release()

    def clear_buffer(self):
        self.buffer = bytearray()

    def receive(self, nbytes, decode='utf-8', timeout=0.1):
        if self.handler is not None:
            raise Exception("Can't call .receive() with an async handler registered!")
        if len(self.buffer) >= nbytes:
            chunk = self.buffer[0:nbytes]
            self.buffer = self.buffer[nbytes:] # put the rest back for later...
            if decode is not None:
                return chunk.decode(decode)
            else:
                return chunk

        self.rxwaitnum = nbytes
        self.rxdoneSem.acquire() # claim

        # now the event handler releases the sem and we can take it again
        suc = self.rxdoneSem.acquire(timeout=timeout)
        # and release it back, to get into a defined state
        self.rxdoneSem.release()

        if not suc:
            if len(self.buffer) < nbytes:
                raise Exception("Data not Rx in timeout!")

        # use the handling code above via recursion
        return self.receive(nbytes, decode, timeout)

