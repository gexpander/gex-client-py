from gex import Client, TF_Msg


class Unit:
    def __init__(self, client:Client, name:str):
        self.client = client
        self.unit_name = name
        self.unit_type = self._type()
        self.callsign = client.get_callsign(name, self.unit_type)

        def evt_hdl(event: int, payload):
            self.on_event(event, payload)

        self.client.bind_report_listener(self.callsign, evt_hdl)

    def _type(self) -> str:
        raise NotImplementedError("Missing _type() in Unit class \"%s\"" % self.__class__.__name__)

    def send(self, cmd:int, pld=None, id:int=None):
        """ Send a command to the unit """
        self.client.send(cs=self.callsign, cmd=cmd, pld=pld, id=id)

    def query(self, cmd:int, pld=None, id:int=None) -> TF_Msg:
        """ Query the unit. Returns TF_Msg """
        return self.client.query(cs=self.callsign, cmd=cmd, pld=pld, id=None)

    def bulk_read(self, cmd:int, pld=None, id:int=None, chunk:int=1024) -> bytearray:
        """
        Perform a bulk read.
        cmd, id and pld are used to initiate the read.
        """
        return self.client.bulk_read(cs=self.callsign, cmd=cmd, id=id, pld=pld, chunk=chunk)

    def bulk_write(self, cmd:int, bulk, id:int=None, pld=None):
        """
        Perform a bulk write.
        cmd, id and pld are used to initiate the read.
        bulk is the data to write.
        """
        self.client.bulk_write(cs=self.callsign, cmd=cmd, id=id, pld=pld, bulk=bulk)

    def on_event(self, event:int, payload):
        """ Stub for an event handler """
        raise NotImplementedError("Missing on_event() in Unit class \"%s\"" % self.__class__.__name__)
