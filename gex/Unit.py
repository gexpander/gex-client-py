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
