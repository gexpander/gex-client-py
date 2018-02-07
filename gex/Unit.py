from gex import Client, TF_Msg
from gex.Client import EventReport


class Unit:
    def __init__(self, client:Client, name:str):
        self.client = client
        self.unit_name = name
        self.unit_type = self._type()
        self.callsign = client.get_callsign(name, self.unit_type)

        # need intermediate function because the method also takes 'self'
        def evt_hdl(evt:EventReport):
            self._on_event(evt)

        self.client.bind_report_listener(self.callsign, evt_hdl)
        self._init()

    def _init(self):
        """ Do post-constructor init """
        pass

    def _type(self) -> str:
        raise NotImplementedError("Missing _type() in Unit class \"%s\"" % self.__class__.__name__)

    def _send(self, cmd:int, pld=None, id:int=None, confirm:bool=False):
        """
        Send a command to the unit.
        If 'confirm' is True, will ask for confirmation and throw an error if not received

        Returns frame ID
        """
        if confirm:
            msg = self._query(cmd|0x80, pld, id)
            return msg.id
        else:
            return self.client.send(cs=self.callsign, cmd=cmd, pld=pld, id=id)

    def _query(self, cmd:int, pld=None, id:int=None) -> TF_Msg:
        """ Query the unit. Returns TF_Msg """
        return self.client.query(cs=self.callsign, cmd=cmd, pld=pld, id=id)

    def _query_async(self, cmd:int, callback, pld=None, id:int=None):
        """
        Query the unit without waiting for response.
        The callback is fired for each frame; returns TF.CLOSE or TF.STAY

        Returns frame ID
        """
        return self.client.query_async(cs=self.callsign, cmd=cmd, pld=pld, id=id, callback=callback)

    def _bulk_read(self, cmd:int, pld=None, id:int=None, chunk:int=1024) -> bytearray:
        """
        Perform a bulk read.
        cmd, id and pld are used to initiate the read.
        """
        return self.client.bulk_read(cs=self.callsign, cmd=cmd, id=id, pld=pld, chunk=chunk)

    def _bulk_write(self, cmd:int, bulk, id:int=None, pld=None):
        """
        Perform a bulk write.
        cmd, id and pld are used to initiate the read.
        bulk is the data to write.
        """
        self.client.bulk_write(cs=self.callsign, cmd=cmd, id=id, pld=pld, bulk=bulk)

    def _on_event(self, evt:EventReport):
        """ Stub for an event handler """
        raise NotImplementedError("Missing _on_event() in Unit class \"%s\"" % self.__class__.__name__)
