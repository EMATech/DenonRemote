# -*- coding: utf-8 -*-
import os
import sys

KIVY_NO_ARGS = 1

import kivy.app
import kivy.core
import kivy.core.window
import kivy.logger
import kivy.resources
import kivy.support
import kivy.uix.behaviors
import kivy.uix.settings
import pystray
from kivy.clock import mainthread

# fix for pyinstaller packages app to avoid ReactorAlreadyInstalledError
# See: https://github.com/kivy/kivy/issues/4182
# See: https://github.com/pyinstaller/pyinstaller/issues/3390
from main import TITLE

if 'twisted.internet.reactor' in sys.modules:
    del sys.modules['twisted.internet.reactor']

# Must be called before importing or using the reactor
kivy.support.install_twisted_reactor()
import twisted.internet
from denon.communication import DenonClientGUIFactory

kivy.require('2.0.0')

logger = kivy.logger.Logger

APP_PATHS = ['fonts', 'images', 'settings']

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

    title: str = TITLE
    """Application title"""

    icon: str = 'icon.png'
    """Application icon"""

    connector: twisted.internet.tcp.Connector = None
    """Twisted connector"""

    client: DenonClientGUIFactory = None
    """Twisted client of the receiver"""

    systray: pystray.Icon = None

    hidden: bool = True if kivy.config.Config.get('graphics', 'window_state') == 'hidden' else False

    settings_cls: kivy.uix.settings.Settings = kivy.uix.settings.SettingsWithSidebar

    def get_application_config(self, **kwargs):
        """
        Store config into user directory
        """
        return super().get_application_config('~/.%(appname)s.ini')

    def build_config(self, config):
        config.adddefaultsection('denonremote')
        from telnetlib import TELNET_PORT
        config.setdefaults('denonremote', {
            'debug': False,
            'receiver_ip': '192.168.x.y',
            'receiver_port': TELNET_PORT,
            'reference_level': '-18',
            'reference_spl': '85',  # SMPTE RP200:2012 & Katz metering system also equivalent to EBU 83dbSPLC@-20dBFS
            'reference_volume': '-18',
            'vol_preset_1': '-30.0dB',
            'vol_preset_2': '-26.0dB',  # K-12
            # -25.0dB  # EBU R 128
            'vol_preset_3': '-24.0dB',  # K-14 / Dolby Home Cinema
            'vol_preset_4': '-18.0dB',  # SMPTE/EBU/Dolby theater
            'fav_src_1_code': 'GAME',
            'fav_src_1_label': 'Computer HDMI',
            'fav_src_2_code': 'CD',
            'fav_src_2_label': 'Pro Analog',
            'fav_src_3_code': 'TV',
            'fav_src_3_label': 'Pro Digital'
        })

    def build_settings(self, settings):
        settings.add_json_panel("Communication", self.config,
                                filename=kivy.resources.resource_find('settings/communication.json'))
        settings.add_json_panel("Volume display", self.config,
                                filename=kivy.resources.resource_find('settings/display.json'))
        settings.add_json_panel("Volume presets", self.config,
                                filename=kivy.resources.resource_find('settings/volume.json'))
        settings.add_json_panel("Favorite source 1", self.config,
                                filename=kivy.resources.resource_find('settings/source1.json'))
        settings.add_json_panel("Favorite source 2", self.config,
                                filename=kivy.resources.resource_find('settings/source2.json'))
        settings.add_json_panel("Favorite source 3", self.config,
                                filename=kivy.resources.resource_find('settings/source3.json'))

    def on_config_change(self, config, section, key, value):
        if config is self.config:
            if section == 'denonremote':
                if key == 'receiver_ip':
                    self._disconnect()
                    self._connect()
                if key == 'vol_preset_1':
                    self.root.ids.vol_preset_1.text = value
                if key == 'vol_preset_2':
                    self.root.ids.vol_preset_2.text = value
                if key == 'vol_preset_3':
                    self.root.ids.vol_preset_3.text = value
                if key == 'vol_preset_4':
                    self.root.ids.vol_preset_4.text = value
                if key == 'fav_src_1_label':
                    self.root.ids.fav_src_1.text = value
                if key == 'fav_src_2_label':
                    self.root.ids.fav_src_2.text = value
                if key == 'fav_src_3_label':
                    self.root.ids.fav_src_3.text = value

    def open_settings(self, *largs):
        self.disable_keyboard_shortcuts()
        super().open_settings()

    def close_settings(self, *largs):
        self.enable_keyboard_shortcuts()
        super().close_settings()

    def run_with_systray(self, systray):
        self.systray = systray
        super().run()

    def _connect(self):
        self.print_debug('Connecting to ' + self.config.get('denonremote', 'receiver_ip') + '...')

        client_factory = DenonClientGUIFactory(self)
        self.connector = twisted.internet.reactor.connectTCP(
            host=self.config.get('denonremote', 'receiver_ip'),
            port=self.config.getint('denonremote', 'receiver_port'),
            factory=client_factory,
            timeout=1)

    def _disconnect(self):
        if self.connector is not None:
            self.print_debug('Disconnecting')
            self.connector = self.connector.disconnect()

    def on_start(self):
        """
        Fired by Kivy on application startup
        :return:
        """
        if self.systray is not None:
            self.systray.visible = True

            # Hide window into systray
            kivy.core.window.Window.bind(on_request_close=self.hide_on_close)
            kivy.core.window.Window.bind(on_minimize=self.hide)

        self.enable_keyboard_shortcuts()

        if not self.config.getboolean('denonremote', 'debug'):
            # Hide debug_messages
            self.root.ids.debug_messages.size = (0, 0)
            # Hide Kivy settings
            self.use_kivy_settings: bool = False

        self._connect()

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
        Fired by the Twisted client when the reactor is connected

        :param connection:
        :return:
        """
        self.print_debug("Connection successful!")
        self.client = connection

        self.client.get_power()
        self.client.get_volume()
        self.client.get_mute()
        self.client.get_source()

        self.root.ids.main.disabled = False

    def on_connection_failed(self, connector, reason):
        if self.connector is connector:
            logger.debug("Connection failed: %s", reason)
            self.print_debug("Connection to receiver failed!")
            # TODO: open error popup
            self.root.ids.main.disabled = True
            self.open_settings()

    def on_connection_lost(self, connector, reason):
        if self.connector is connector:
            logger.debug("Connection lost: %s", reason)
            self.print_debug("Connection to receiver lost!")
            # TODO: open error popup

            self.root.ids.main.disabled = True

    @mainthread
    def show(self, window=None):
        if window is None:
            window = self.root_window
        window.restore()
        window.show()
        window.raise_window()
        self.hidden = False

    @mainthread
    def hide(self, window=None):
        if window is None:
            window = self.root_window
        window.hide()
        self.hidden = True

    def hide_on_close(self, window, source=None):
        logger.debug("Hide from %s", source)
        self.hide(window)
        return True  # Keeps the application alive instead of stopping

    def enable_keyboard_shortcuts(self):
        kivy.core.window.Window.bind(on_keyboard=self.on_keyboard)

    def disable_keyboard_shortcuts(self):
        kivy.core.window.Window.unbind(on_keyboard=self.on_keyboard)

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        """
        Handle keyboard shortcuts

        :param window:
        :param key:
        :param scancode:
        :param codepoint:
        :param modifier:
        :return:
        """
        logger.debug("key: %s, scancode: %s, codepoint: %s, modifier: %s", key, scancode, codepoint, modifier)
        if codepoint == 'm':
            self.root.ids.volume_mute.trigger_action()
        if scancode == 82:  # Up
            self.root.ids.volume_plus.trigger_action()
        if scancode == 81:  # Down
            self.root.ids.volume_minus.trigger_action()

    def update_power(self, status=True):
        if status:
            self.root.ids.power.state = 'down'
        else:
            self.root.ids.power.state = 'normal'

    def power_pressed(self, instance):
        power = False if instance.state == 'normal' else True
        self.client.set_power(power)

    def update_volume(self, text="", ref_level=None):
        # If we get no text, retrieve the currently displayed one
        if text == "":
            text = self.root.ids.volume_display.text
        else:
            # We don't need to update the volume display if no text is passed
            self.root.ids.volume_display.text = text
            if text in self.config.get('denonremote', 'vol_preset_1'):
                self.root.ids.vol_preset_1.state = 'down'
            else:
                self.root.ids.vol_preset_1.state = 'normal'
            if text in self.config.get('denonremote', 'vol_preset_2'):
                self.root.ids.vol_preset_2.state = 'down'
            else:
                self.root.ids.vol_preset_2.state = 'normal'
            if text in self.config.get('denonremote', 'vol_preset_3'):
                self.root.ids.vol_preset_3.state = 'down'
            else:
                self.root.ids.vol_preset_3.state = 'normal'
            if text in self.config.get('denonremote', 'vol_preset_4'):
                self.root.ids.vol_preset_4.state = 'down'
            else:
                self.root.ids.vol_preset_4.state = 'normal'

        # Retrieve the displayed reference level if not passed
        if ref_level is None:
            # Get pressed option
            mode_ref_widgets = kivy.uix.behaviors.togglebutton.ToggleButtonBehavior.get_widgets('mode_ref')
            active_widget = next(widget for widget in mode_ref_widgets if widget.state == 'down')
            ref_level = self._get_mode_level(active_widget.text)

        # Update the SPL display
        (spl_text, ref_text) = self._compute_spl_text(text, ref_level)
        self.root.ids.spl_display.text = spl_text
        self.root.ids.ref_display.text = ref_text

    def _compute_spl_text(self, text="", ref_level=-18):
        # FIXME: Handle Absolute mode
        # Relative mode computation
        volume = float(text[:-2])  # strip dB
        volume_delta = volume - float(
            self.config.get('denonremote', 'reference_volume'))  # compute delta with reference volume
        spl = int(round(
            float(self.config.get('denonremote', 'reference_spl')) + volume_delta))  # apply delta to reference SPL
        # Reference mode handling
        ref_delta = ref_level - int(
            self.config.get('denonremote', 'reference_level'))  # compute delta with reference level
        spl = spl + ref_delta
        spl_text = "%i dB SPL" % spl  # format string with computed SPL and reference level mode
        ref_text = "@ %i dBFS" % ref_level
        text = (spl_text, ref_text)
        return text

    def mode_changed(self, instance):
        level = self._get_mode_level(instance.text)
        self.update_volume(ref_level=level)

    @staticmethod
    def _get_mode_level(instance_text):
        level = -18  # We default to EBU
        if instance_text == 'EBU R 128':
            level = -23  # LUFS
        elif instance_text == 'K-20':
            level = -20  # dBFS
        elif instance_text == 'EBU/SMPTE':
            level = -18  # dBFS
        elif instance_text == 'K-14':
            level = -14  # dBFS
        elif instance_text == 'K-12':
            level = -12  # dBFS
        return level

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
        self.client.set_volume(self.config.get('denonremote', 'vol_preset_1'))
        instance.state = 'down'  # Disallow depressing the button manually

    def vol_preset_2_pressed(self, instance):
        self.client.set_volume(self.config.get('denonremote', 'vol_preset_2'))
        instance.state = 'down'

    def vol_preset_3_pressed(self, instance):
        self.client.set_volume(self.config.get('denonremote', 'vol_preset_3'))
        instance.state = 'down'

    def vol_preset_4_pressed(self, instance):
        self.client.set_volume(self.config.get('denonremote', 'vol_preset_4'))
        instance.state = 'down'

    def set_sources(self, source=None):
        if source in self.config.get('denonremote', 'fav_src_1_code'):
            self.root.ids.fav_src_1.state = 'down'
        else:
            self.root.ids.fav_src_1.state = 'normal'
        if source in self.config.get('denonremote', 'fav_src_2_code'):
            self.root.ids.fav_src_2.state = 'down'
        else:
            self.root.ids.fav_src_2.state = 'normal'
        if source in self.config.get('denonremote', 'fav_src_3_code'):
            self.root.ids.fav_src_3.state = 'down'
        else:
            self.root.ids.fav_src_3.state = 'normal'

        # TODO: display other sources

    def fav_src_1_pressed(self, instance):
        self.client.set_source(self.config.get('denonremote', 'fav_src_1_code'))
        instance.state = 'down'  # Disallow depressing the button manually

    def fav_src_2_pressed(self, instance):
        self.client.set_source(self.config.get('denonremote', 'fav_src_2_code'))
        instance.state = 'down'

    def fav_src_3_pressed(self, instance):
        self.client.set_source(self.config.get('denonremote', 'fav_src_3_code'))
        instance.state = 'down'

    def print_debug(self, msg):
        self.root.ids.debug_messages.text += "{}\n".format(msg)
