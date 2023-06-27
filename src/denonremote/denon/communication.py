# This Python file uses the following encoding: utf-8
#
# SPDX-FileCopyrightText: 2021-2023 Raphaël Doursenaud <rdoursenaud@free.fr>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from typing import TYPE_CHECKING

import twisted.internet.interfaces
import twisted.python.failure
from twisted.internet import reactor, task
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineOnlyReceiver
from twisted.protocols.policies import TimeoutMixin

from .dn500av import DN500AVFormat, DN500AVMessage

if TYPE_CHECKING:
    from denonremote.gui import DenonRemoteApp

logger = logging.getLogger(__name__)


# TODO: Implement Serial ?
# See: https://twistedmatrix.com/documents/15.4.0/api/twisted.internet.serialport.SerialPort.html


class DenonProtocol(LineOnlyReceiver, TimeoutMixin):
    # From DN-500 manual (DN-500AVEM_ENG_CD-ROM_v00.pdf) page 91 (97 in PDF form)
    MAX_LENGTH: int = 135
    DELAY: float = .2
    """
    Delay between messages in seconds.
    The documentation requires 200 ms.
    20 ms seems safe.
    """
    DEFAULT_TIMEOUT: float = .2
    """
    Changing sources takes way more than 200ms.
    Let's bump this case to 5 seconds to prevent spurious disconnections.
    """
    delimiter: bytes
    factory: 'DenonClientFactory'
    ongoing_calls: int
    timeOut: float
    transport: twisted.internet.interfaces.ITCPTransport

    def __init__(self):
        self.delimiter = b'\r'
        self.ongoing_calls = 0  # Delay handling.

    def connectionMade(self) -> None:
        logger.debug("Connection made")
        if self.factory.gui:
            self.factory.app.on_connection(self)

    def timeoutConnection(self) -> None:
        logger.debug("Connection timed out")
        self.transport.abortConnection()
        if self.factory.gui:
            self.factory.app.on_timeout()

    def sendLine(self, line: bytes) -> task.Deferred | None:
        deferred = None
        line_len = len(line)
        if line_len > self.MAX_LENGTH:
            logger.warning(f'Line too long (>{self.MAX_LENGTH}): {line_len}')
        if b'?' not in line:
            logger.debug(f"Sending line: {line.decode('ASCII')}")
            super().sendLine(line)
        else:
            # A request is made. We need to delay the next calls
            self.ongoing_calls += 1
            logger.debug(f'Ongoing calls for delay: {self.ongoing_calls}')
            delay = 0  # Send now
            if self.ongoing_calls > 0:
                delay = self.DELAY * (self.ongoing_calls - 1)  # Send after other messages
            logger.debug(f"Will send line: {line} in {delay} seconds")
            deferred = task.deferLater(
                reactor,
                delay=delay,
                callable=self.sendLineWithTimeout,
                line=line,
            )
        return deferred

    # noinspection PyPep8Naming
    def sendLineWithTimeout(self, line: bytes) -> None:
        timeout = self.DEFAULT_TIMEOUT
        if self.timeOut:
            timeout += self.timeOut
        self.setTimeout(timeout)
        logger.debug(f"Sending line with timeout ({timeout} s): {line.decode('ASCII')}")
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
        raw_value = DN500AVFormat().mv_reverse_params.get(value)
        if raw_value is None:
            logger.warning(f"Set volume value {value} is invalid.")
        else:
            message = 'MV' + raw_value
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
    gui: bool
    protocol = DenonProtocol

    def __init__(self) -> None:
        self.gui = False


class DenonClientGUIFactory(ClientFactory):
    app: 'DenonRemoteApp'  # TODO: Extract interface
    protocol = DenonProtocol

    def __init__(self, app) -> None:
        self.gui = True
        self.app = app
        import kivy.logger
        global logger
        logger = kivy.logger.Logger

    def clientConnectionFailed(
            self, connector: twisted.internet.interfaces.IConnector,
            reason: twisted.python.failure.Failure
    ) -> None:
        self.app.on_connection_failed(connector, reason)

    def clientConnectionLost(
            self, connector: twisted.internet.interfaces.IConnector,
            reason: twisted.python.failure.Failure
    ) -> None:
        self.app.on_connection_lost(connector, reason)
