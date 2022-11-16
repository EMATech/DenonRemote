# This Python file uses the following encoding: utf-8
#
# SPDX-FileCopyrightText: 2021-2022 Raphaël Doursenaud <rdoursenaud@free.fr>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Denon Remote Command Line Interface mode.
"""

import kivy.config
from twisted.internet import reactor

from denonremote.denon.communication import DenonClientFactory


class DenonRemoteApp:
    def run(self):
        # Get from config
        # FIXME: or get from arguments
        receiver_ip = kivy.config.get('denonremote', 'receiver_ip')
        receiver_port = kivy.config.get('denonremote', 'receiver_port')

        reactor.connectTCP(receiver_ip, receiver_port, DenonClientFactory())
        reactor.run()
