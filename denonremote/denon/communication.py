# -*- coding: utf-8 -*-

import logging

from twisted.internet import task, reactor
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineOnlyReceiver

from denon.dn500av import DN500AVMessage, DN500AVFormat

logger = logging.getLogger(__name__)


# TODO: Implement Serial ?
# See: https://twistedmatrix.com/documents/15.4.0/api/twisted.internet.serialport.SerialPort.html


class DenonProtocol(LineOnlyReceiver):
    # From DN-500 manual (DN-500AVEM_ENG_CD-ROM_v00.pdf) page 91 (97 in PDF form)
    MAX_LENGTH = 135
    DELAY = 0.04  # in seconds. The documentation requires 200 ms. 40 ms seems safe.
    delimiter = b'\r'
    ongoing_calls = 0  # Delay handling. FIXME: should timeout after 200 ms.

    def connectionMade(self):
        logger.debug("Connection made")
        if self.factory.gui:
            self.factory.app.on_connection(self)

    def timeoutConnection(self):
        logger.debug("Connection timed out")
        self.transport.abortConnection()
        if self.factory.gui:
            self.factory.app.on_timeout()

    def sendLine(self, line):
        if b'?' in line:
            # A request is made. We need to delay the next calls
            self.ongoing_calls += 1
            logger.debug("Ongoing calls for delay: %s", self.ongoing_calls)
        delay = 0
        if self.ongoing_calls > 0:
            delay = self.DELAY * (self.ongoing_calls - 1)
        logger.debug("Will send line: %s in %f seconds", line, delay)
        return task.deferLater(reactor, delay=delay,
                               callable=super().sendLine, line=line)

    def lineReceived(self, line):
        if self.ongoing_calls:
            # We received a reply
            self.ongoing_calls -= 1
            logger.debug("Ongoing calls for delay: %s", self.ongoing_calls)
        receiver = DN500AVMessage()
        receiver.parse_response(line)
        logger.info("Received line: %s", receiver.response)

        # FIXME: parse message into state

        # FIXME: abstract away with a callback to the factory
        if self.factory.gui:
            self.factory.app.print_debug(receiver.response)

            # POWER
            if receiver.command_code == 'PW':
                state = True
                if receiver.parameter_code == 'STANDBY':
                    state = False
                self.factory.app.update_power(state)

            # VOLUME
            if receiver.command_code == 'MV':
                if receiver.subcommand_code is None:
                    self.factory.app.update_volume(receiver.parameter_label)

            # MUTE
            if receiver.command_code == 'MU':
                state = False
                if receiver.parameter_code == 'ON':
                    state = True
                self.factory.app.set_volume_mute(state)

            # SOURCE
            if receiver.command_code == 'SI':
                source = receiver.parameter_code
                self.factory.app.set_sources(source)

    def get_power(self):
        self.sendLine('PW?'.encode('ASCII'))

    def set_power(self, state):
        logger.debug("Entering power callback")
        if state:
            self.sendLine('PWON'.encode('ASCII'))
        else:
            self.sendLine('PWSTANDBY'.encode('ASCII'))

    def get_volume(self):
        self.sendLine('MV?'.encode('ASCII'))

    def set_volume(self, value):
        rawvalue = DN500AVFormat().mv_reverse_params.get(value)
        if rawvalue is None:
            logger.warning("Set volume value %s is invalid.", value)
        else:
            message = 'MV' + rawvalue
            self.sendLine(message.encode('ASCII'))

    def get_mute(self):
        self.sendLine('MU?'.encode('ASCII'))

    def set_mute(self, state):
        if state:
            self.sendLine('MUON'.encode('ASCII'))
        else:
            self.sendLine('MUOFF'.encode('ASCII'))

    def get_source(self):
        self.sendLine('SI?'.encode('ASCII'))

    def set_source(self, source):
        message = 'SI' + source
        self.sendLine(message.encode('ASCII'))


class DenonClientFactory(ClientFactory):
    protocol = DenonProtocol

    def __init__(self):
        self.gui = False


class DenonClientGUIFactory(ClientFactory):
    protocol = DenonProtocol

    def __init__(self, app):
        self.gui = True
        self.app = app
        import kivy.logger
        global logger
        logger = kivy.logger.Logger

    def clientConnectionFailed(self, connector, reason):
        self.app.on_connection_failed(connector, reason)

    def clientConnectionLost(self, connector, reason):
        self.app.on_connection_lost(connector, reason)
