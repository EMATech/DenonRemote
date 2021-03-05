# -*- coding: utf-8 -*-
import os
import sys

import kivy.app
import kivy.resources
import kivy.support

# FIXME: should be in Config object?
from config import RECEIVER_IP, RECEIVER_PORT, VOL_PRESET_1, VOL_PRESET_2, VOL_PRESET_3, FAV_SRC_1_CODE, \
    FAV_SRC_2_CODE, FAV_SRC_3_CODE, DEBUG

# fix for pyinstaller packages app to avoid ReactorAlreadyInstalledError
# See: https://github.com/kivy/kivy/issues/4182
# See: https://github.com/pyinstaller/pyinstaller/issues/3390
if 'twisted.internet.reactor' in sys.modules:
    del sys.modules['twisted.internet.reactor']

# Must be called before importing or using the reactor
kivy.support.install_twisted_reactor()
import twisted.internet
from denon.communication import DenonClientGUIFactory

kivy.require('2.0.0')

# Fixed size window
kivy.Config.set('graphics', 'resizable', False)

APP_PATHS = ['fonts', 'images']

# PyInstaller data support
for path in APP_PATHS:
    if hasattr(sys, '_MEIPASS'):
        kivy.resources.resource_add_path(os.path.join(sys._MEIPASS, path))
    else:
        kivy.resources.resource_add_path(path)


class DenonRemoteApp(kivy.app.App):
    """
    A remote for the Denon DN-500AV Receiver
    """

    client = None
    """Twisted IP client to the receiver"""

    title = "Denon Remote"
    """Application title"""

    icon = 'icon.png'
    """Application icon"""

    def on_start(self):
        """
        Fired by Kivy on application startup
        :return:
        """
        if not DEBUG:
            # Hide debug_messages
            self.root.ids.debug_messages.size = (0, 0)

        self.print_debug('Connecting to ' + RECEIVER_IP + '...')
        twisted.internet.reactor.connectTCP(RECEIVER_IP, RECEIVER_PORT, DenonClientGUIFactory(self))

    def on_stop(self):
        """
        Fired by Kivy on application shutdown

        :return:
        """
        pass

    def on_pause(self):
        """
        Fired by Kivy on application pause

        :return:
        """
        pass

    def on_resume(self):
        """
        Fired by Kivy on application resume after pause

        :return:
        """
        pass

    def on_connection(self, connection):
        """
        Fired by Kivy when the Twisted reactor is connected

        :param connection:
        :return:
        """
        self.print_debug('Connection successful!')
        self.client = connection

        self.client.get_power()
        self.client.get_volume()
        self.client.get_mute()
        self.client.get_source()

    def update_power(self, status=True):
        if status:
            self.root.ids.power.state = 'down'
        else:
            self.root.ids.power.state = 'normal'

    def power_pressed(self, instance):
        power = False if instance.state == 'normal' else True
        self.client.set_power(power)

    def update_volume(self, text=""):
        self.root.ids.volume_display.text = text
        if text in VOL_PRESET_1:
            self.root.ids.vol_preset_1.state = 'down'
        else:
            self.root.ids.vol_preset_1.state = 'normal'
        if text in VOL_PRESET_2:
            self.root.ids.vol_preset_2.state = 'down'
        else:
            self.root.ids.vol_preset_2.state = 'normal'
        if text in VOL_PRESET_3:
            self.root.ids.vol_preset_3.state = 'down'
        else:
            self.root.ids.vol_preset_3.state = 'normal'

    def volume_text_changed(self, instance):
        # TODO: validate user input
        if len(instance.text) != 7:
            self.client.get_volume()
            return
        self.client.set_volume(instance.text)

    def volume_minus_pressed(self, instance):
        self.client.set_volume('Down')

    def volume_plus_pressed(self, instance):
        self.client.set_volume('Up')

    def volume_mute_pressed(self, instance):
        mute = True if instance.state == 'down' else False
        # Stay down. Updated on message received
        self.root.ids.volume_mute.state = 'down'
        self.client.set_mute(mute)

    def set_volume_mute(self, status=False):
        if status:
            self.root.ids.volume_mute.state = 'down'
            self.root.ids.volume_display.foreground_color = [.3, .3, .3, 1]
        else:
            self.root.ids.volume_mute.state = 'normal'
            self.root.ids.volume_display.foreground_color = [.85, .85, .85, 1]

    def vol_preset_1_pressed(self, instance):
        self.client.set_volume(VOL_PRESET_1)
        instance.state = 'down'  # Disallow depressing the button manually

    def vol_preset_2_pressed(self, instance):
        self.client.set_volume(VOL_PRESET_2)
        instance.state = 'down'

    def vol_preset_3_pressed(self, instance):
        self.client.set_volume(VOL_PRESET_3)
        instance.state = 'down'

    def set_sources(self, source=None):
        if source in FAV_SRC_1_CODE:
            self.root.ids.fav_src_1.state = 'down'
        else:
            self.root.ids.fav_src_1.state = 'normal'
        if source in FAV_SRC_2_CODE:
            self.root.ids.fav_src_2.state = 'down'
        else:
            self.root.ids.fav_src_2.state = 'normal'
        if source in FAV_SRC_3_CODE:
            self.root.ids.fav_src_3.state = 'down'
        else:
            self.root.ids.fav_src_3.state = 'normal'

        # TODO: display other sources

    def fav_src_1_pressed(self, instance):
        self.client.set_source(FAV_SRC_1_CODE)
        instance.state = 'down'  # Disallow depressing the button manually

    def fav_src_2_pressed(self, instance):
        self.client.set_source(FAV_SRC_2_CODE)
        instance.state = 'down'

    def fav_src_3_pressed(self, instance):
        self.client.set_source(FAV_SRC_3_CODE)
        instance.state = 'down'

    def print_debug(self, msg):
        self.root.ids.debug_messages.text += "{}\n".format(msg)
