from plasmoid.modules import PlasmoidModule
import socket

class Network(PlasmoidModule):
    def __init__(self):
        self.add_producer('addresses',self.get_ip)

    def get_ip(self):
        ret = {
            'hostname': socket.gethostname(),
            'ip':[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
        }
        return ret