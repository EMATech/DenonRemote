# This Python file uses the following encoding: utf-8
#
# SPDX-FileCopyrightText: 2021-2022 Raphaël Doursenaud <rdoursenaud@free.fr>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

import twisted.internet.interfaces
import twisted.python.failure
from twisted.internet import task, reactor
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineOnlyReceiver
from twisted.protocols.policies import TimeoutMixin

from .dn500av import DN500AVMessage, DN500AVFormat

logger = logging.getLogger(__name__)


# TODO: Implement Serial ?
# See: https://twistedmatrix.com/documents/15.4.0/api/twisted.internet.serialport.SerialPort.html


class DenonProtocol(LineOnlyReceiver, TimeoutMixin):
    # From DN-500 manual (DN-500AVEM_ENG_CD-ROM_v00.pdf) page 91 (97 in PDF form)
    MAX_LENGTH = 135
    DELAY = 0.04
    """
    Delay between messages in seconds.
    The documentation requires 200 ms. 40 ms seems safe.
    """
    TIMEOUT = .2
    """
    Requests shall time out if no reply is received in under 200 ms.
    """
    EXTENDED_TIMEOUT = 5
    """
    Changing sources takes way more than 200ms.
    Let's bump this case to 5 seconds to prevent spurious disconnections.
    """
    delimiter = b'\r'
    ongoing_calls = 0  # Delay handling.

    def connectionMade(self) -> None:
        logger.debug("Connection made")
        if self.factory.gui:
            self.factory.app.on_connection(self)

    def timeoutConnection(self) -> None:
        logger.debug("Connection timed out")
        self.transport.abortConnection()
        if self.factory.gui:
            self.factory.app.on_timeout()

    def sendLine(self, line: bytes) -> task.Deferred:
        if b'?' in line:
            # A request is made. We need to delay the next calls
            self.ongoing_calls += 1
            logger.debug(f'Ongoing calls for delay: {self.ongoing_calls}')
        delay = 0  # Send now
        if self.ongoing_calls > 0:
            delay = self.DELAY * (self.ongoing_calls - 1)  # Send after other messages
        logger.debug(f"Will send line: {line} in {delay} seconds")
        line_len = len(line)
        if line_len > self.MAX_LENGTH:
            logger.warning(f'Line too long (>{self.MAX_LENGTH}): {line_len}')
        return task.deferLater(reactor, delay=delay,
                               callable=self.sendLineWithTimeout, line=line)

    # noinspection PyPep8Naming
    def sendLineWithTimeout(self, line: bytes) -> None:
        timeout = self.TIMEOUT
        if b'SI' in line:
            timeout = self.EXTENDED_TIMEOUT
        self.setTimeout(timeout)
        logger.debug(f'Send accumulated timeout: {self.timeOut}')
        super().sendLine(line)

    def lineReceived(self, line: bytes) -> None:
        if self.ongoing_calls:
            # We received a reply
            self.resetTimeout()
            self.ongoing_calls -= 1
            logger.debug(f"Ongoing calls for delay: {self.ongoing_calls}")
        else:
            # Disable timeout, we don't expect any other command.
            self.setTimeout(None)
        logger.debug(f"Receive remaining timeout: {self.timeOut}")
        receiver = DN500AVMessage()
        receiver.parse_response(line)
        logger.info(f"Received line: {receiver.response}")

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
                elif receiver.subcommand_code == 'MAX':
                    self.factory.app.update_max_volume(receiver.parameter_label)

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

    def get_power(self) -> None:
        self.sendLine('PW?'.encode('ASCII'))

    def set_power(self, state: bool) -> None:
        logger.debug("Entering power callback")
        if state:
            self.sendLine('PWON'.encode('ASCII'))
        else:
            self.sendLine('PWSTANDBY'.encode('ASCII'))

    def get_volume(self) -> None:
        self.sendLine('MV?'.encode('ASCII'))

    def set_volume(self, value: str) -> None:
        rawvalue = DN500AVFormat().mv_reverse_params.get(value)
        if rawvalue is None:
            logger.warning(f"Set volume value {value} is invalid.")
        else:
            message = 'MV' + rawvalue
            self.sendLine(message.encode('ASCII'))

    def get_mute(self) -> None:
        self.sendLine('MU?'.encode('ASCII'))

    def set_mute(self, state: bool) -> None:
        if state:
            self.sendLine('MUON'.encode('ASCII'))
        else:
            self.sendLine('MUOFF'.encode('ASCII'))

    def get_source(self) -> None:
        self.sendLine('SI?'.encode('ASCII'))

    def set_source(self, source: str) -> None:
        message = 'SI' + source
        self.sendLine(message.encode('ASCII'))


class DenonClientFactory(ClientFactory):
    protocol = DenonProtocol

    def __init__(self) -> None:
        self.gui = False


class DenonClientGUIFactory(ClientFactory):
    protocol = DenonProtocol

    def __init__(self, app) -> None:
        self.gui = True
        self.app = app
        import kivy.logger
        global logger
        logger = kivy.logger.Logger

    def clientConnectionFailed(self, connector: twisted.internet.interfaces.IConnector,
                               reason: twisted.python.failure.Failure) -> None:
        self.app.on_connection_failed(connector, reason)

    def clientConnectionLost(self, connector: twisted.internet.interfaces.IConnector,
                             reason: twisted.python.failure.Failure) -> None:
        self.app.on_connection_lost(connector, reason)
