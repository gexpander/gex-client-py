from gex import Client

class Unit:
    def __init__(self, client :Client, name :str, type :str):
        self.client = client
        self.unit_name = name
        self.unit_type = type
        self.callsign = client.get_callsign(name, type)

    def send(self, cmd, pld=None, id=None):
        """ Send a command to the unit """
        self.client.send(cs=self.callsign, cmd=cmd, pld=pld, id=id)

    def query(self, cmd, pld=None, id=None):
        """ Query the unit. Returns TF_Msg """
        self.client.query(cs=self.callsign, cmd=cmd, pld=pld, id=None)

    def bulk_read(self, cmd, id=None, pld=None, chunk=1024):
        """
        Perform a bulk read.
        cmd, id and pld are used to initiate the read.
        """
        self.client.bulk_read(cs=self.callsign, cmd=cmd, id=id, pld=pld, chunk=chunk)

    def bulk_write(self, cmd, bulk, id=None, pld=None):
        """
        Perform a bulk write.
        cmd, id and pld are used to initiate the read.
        bulk is the data to write.
        """
        self.client.bulk_write(cs=self.callsign, cmd=cmd, id=id, pld=pld, bulk=bulk)
