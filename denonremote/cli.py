import kivy.config
from twisted.internet import reactor

from denon.communication import DenonClientFactory


class DenonRemoteApp:
    def run(self):
        # Get from config
        # FIXME: or get from arguments
        receiver_ip = kivy.config.Config.get('denonremote', 'receiver_ip')
        receiver_port = kivy.config.Config.get('denonremote', 'receiver_port')

        reactor.connectTCP(receiver_ip, receiver_port, DenonClientFactory())
        reactor.run()
