from twisted.internet import reactor

from config import RECEIVER_IP, RECEIVER_PORT
from denon.communication import DenonClientFactory


class DenonRemoteApp:
    def run(self):
        reactor.connectTCP(RECEIVER_IP, RECEIVER_PORT, DenonClientFactory())
        reactor.run()
