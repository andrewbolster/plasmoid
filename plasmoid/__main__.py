from plasmoid.mqtt import PlasmoidMQTTHandler
from plasmoid.modules.sensehat import SenseHat
from plasmoid.modules.networking import Network

def launch():
    application = PlasmoidMQTTHandler(modules=[SenseHat(), Network()])
    application.main()

if __name__ == '__main__':
    launch()