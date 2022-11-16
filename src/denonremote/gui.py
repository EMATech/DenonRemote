# This Python file uses the following encoding: utf-8
#
# SPDX-FileCopyrightText: 2021-2022 Raphaël Doursenaud <rdoursenaud@free.fr>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Denon Remote GUI.
"""

import os
import sys

# Don't pass CLI arguments to Kivy.
# Must be set before importing Kivy.
os.environ['KIVY_NO_ARGS'] = '1'

import configparser
import kivy.app
import kivy.clock
import kivy.core
import kivy.core.window
import kivy.logger
import kivy.resources
import kivy.uix.behaviors
import kivy.uix.settings
import kivy.uix.widget
import KivyOnTop
import pystray
import win32gui
import win32con

# Must be called before importing or using the reactor
from kivy.support import install_twisted_reactor

install_twisted_reactor()
import twisted.internet
import twisted.internet.tcp
import twisted.python.failure

from denonremote.__about__ import __TITLE__
from denonremote.denon.communication import DenonClientGUIFactory
from kivy.animation import Animation
from kivy.uix.togglebutton import ToggleButton
from telnetlib import TELNET_PORT

kivy.require('2.1.0')

logger = kivy.logger.Logger

# PyInstaller data support
for path in ['fonts', 'images', 'settings']:
    if hasattr(sys, '_MEIPASS'):
        # noinspection PyProtectedMember
        kivy.resources.resource_add_path(os.path.join(sys._MEIPASS, path))
    else:
        kivy.resources.resource_add_path(path)

_BACKOFF = .05

WIDTH = 800
HEIGHT = 600
SMALL_HEIGHT = 60


class PowerButton(ToggleButton):
    """
    Power button

    With blink animation.
    """
    speed = 1  # seconds

    def __init__(self, **kwargs):
        self.anim = Animation(opacity=0, duration=self.speed, t='in_out_cubic')
        self.anim += Animation(opacity=1, duration=self.speed, t='in_out_cubic')
        self.anim.repeat = True
        super().__init__(**kwargs)

    def blink(self, start=True):
        if start:
            self.anim.start(self)
        else:
            self.anim.stop(self)
            self.opacity = 1


class DenonRemoteApp(kivy.app.App):
    """
    A remote for the Denon DN-500AV Receiver
    """

    title: str = __TITLE__
    """Application title"""

    icon: str = 'icon.png'
    """Application icon"""

    connector: None | twisted.internet.tcp.Connector = None
    """Twisted connector"""

    _backoff: float = _BACKOFF
    """Retry failed or lost connection with exponential backoff"""

    client: None | DenonClientGUIFactory = None
    """Twisted client of the receiver"""

    systray: None | pystray.Icon = None

    hidden: bool = bool(kivy.config.Config.get('graphics', 'window_state') == 'hidden')

    settings_cls: kivy.uix.settings.Settings = kivy.uix.settings.SettingsWithSidebar

    maximum_volume = '  0.0dB'

    def build_config(self, config: configparser.ConfigParser) -> None:
        config.adddefaultsection('denonremote')
        config.setdefaults('denonremote', {
            'debug': False,
            'receiver_ip': '192.168.x.y',
            'receiver_port': TELNET_PORT,
            'always_on_top': True,
            'reference_level': '-20',  # SMPTE RP200:2012 & Katz metering system also equivalent to EBU 83dbSPLC@-20dBFS
            'reference_spl': '83',
            'reference_volume': '-18',  # The best alignment level with my current setup (Dynaudio BM5A)
            'vol_preset_1': '-30.0dB',  # My preferred leisure level
            'vol_preset_2': '-26.0dB',  # K-12
            # -25.0dB  # EBU R 128
            'vol_preset_3': '-24.0dB',  # K-14 / Dolby Home Cinema
            'vol_preset_4': '-18.0dB',  # SMPTE/EBU/Dolby theater (Reference volume)
            'fav_src_1_code': 'GAME',
            'fav_src_1_label': "Computer HDMI",
            'fav_src_2_code': 'CD',
            'fav_src_2_label': "Pro Analog",
            'fav_src_3_code': 'TV',
            'fav_src_3_label': "Pro Digital",
            'fav_src_4_code': '',
            'fav_src_4_label': "",
            'fav_src_5_code': '',
            'fav_src_5_label': "",
            'fav_src_6_code': '',
            'fav_src_6_label': "",
        })

    def build_settings(self, settings: kivy.uix.settings.Settings) -> None:
        settings.add_json_panel("Communication", self.config,
                                filename=kivy.resources.resource_find('communication.json'))
        settings.add_json_panel("Window", self.config,
                                filename=kivy.resources.resource_find('window.json'))
        settings.add_json_panel("Volume display", self.config,
                                filename=kivy.resources.resource_find('volume_display.json'))
        settings.add_json_panel("Volume presets", self.config,
                                filename=kivy.resources.resource_find('volume.json'))
        settings.add_json_panel("Favorite source 1", self.config,
                                filename=kivy.resources.resource_find('source1.json'))
        settings.add_json_panel("Favorite source 2", self.config,
                                filename=kivy.resources.resource_find('source2.json'))
        settings.add_json_panel("Favorite source 3", self.config,
                                filename=kivy.resources.resource_find('source3.json'))
        settings.add_json_panel("Favorite source 4", self.config,
                                filename=kivy.resources.resource_find('source4.json'))
        settings.add_json_panel("Favorite source 5", self.config,
                                filename=kivy.resources.resource_find('source5.json'))
        settings.add_json_panel("Favorite source 6", self.config,
                                filename=kivy.resources.resource_find('source6.json'))

    def get_application_config(self, _: str = '%(appdir)s/%(appname)s.ini') -> None:
        """
        Store config into user directory
        """
        return super().get_application_config('~/.%(appname)s.ini')

    def on_config_change(self, config: configparser.ConfigParser, section: str, key: str, value: str) -> None:
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
                if key == 'fav_src_4_label':
                    self.root.ids.fav_src_4.text = value
                if key == 'fav_src_5_label':
                    self.root.ids.fav_src_5.text = value
                if key == 'fav_src_6_label':
                    self.root.ids.fav_src_6.text = value

    def open_settings(self, *_) -> None:
        self.disable_keyboard_shortcuts()
        super().open_settings()

    def close_settings(self, *_) -> None:
        self.enable_keyboard_shortcuts()
        super().close_settings()

    def run_with_systray(self, systray: pystray.Icon) -> None:
        self.systray = systray
        super().run()

    def _connect(self, *_) -> None:
        self.print_debug('Connecting to ' + self.config.get('denonremote', 'receiver_ip') + '...', True)

        client_factory = DenonClientGUIFactory(self)
        self.connector = twisted.internet.reactor.connectTCP(
            host=self.config.get('denonremote', 'receiver_ip'),
            port=self.config.getint('denonremote', 'receiver_port'),
            factory=client_factory,
            timeout=1)

    def _disconnect(self) -> None:
        if self.connector is not None:
            self.print_debug('Disconnecting', True)
            self.connector.disconnect()
            self.connector = None

    def on_timeout(self) -> None:
        pass

    def on_start(self) -> None:
        """
        Fired by Kivy on application startup
        :return:
        """

        print(self.root)

        # FIXME: Windows only ATM.
        if self.config.getboolean('denonremote', 'always_on_top'):
            KivyOnTop.register_topmost(kivy.core.window.Window, __TITLE__)
            kivy.core.window.Window.bind(on_stop=
                                         lambda *args, w=kivy.core.window.Window,
                                                t=__TITLE__: KivyOnTop.unregister_topmost(w, t))

        # Don’t steal focus
        win32gui.SetWindowLong(KivyOnTop.find_hwnd(__TITLE__), win32con.GWL_EXSTYLE, win32con.WS_EX_NOACTIVATE)

        # Raise when mouse enters
        kivy.core.window.Window.bind(on_cursor_enter=lambda *_: kivy.core.window.Window.raise_window())

        # Custom titlebar
        kivy.core.window.Window.custom_titlebar = True
        kivy.core.window.Window.set_custom_titlebar(self.root.ids.header)

        if self.systray is not None:
            self.systray.visible = True

            # Hide window into systray
            kivy.core.window.Window.bind(on_request_close=self.hide_on_close)
            kivy.core.window.Window.bind(on_minimize=self.hide)

        self.enable_keyboard_shortcuts()

        if not self.config.getboolean('denonremote', 'debug'):
            # Hide debug_messages
            self.root.ids.debug_messages.opacity = 0
            self.root.ids.debug_messages.disabled = True
            # Hide Kivy settings
            self.use_kivy_settings: bool = False

        self._connect()

    def on_stop(self) -> None:
        """
        Fired by Kivy on application shutdown

        :return:
        """
        pass

    def on_pause(self) -> None:
        """
        Fired by Kivy on application pause

        :return:
        """
        pass

    def on_resume(self) -> None:
        """
        Fired by Kivy on application resume after pause

        :return:
        """
        pass

    def on_connection(self, connection: DenonClientGUIFactory) -> None:
        """
        Fired by the Twisted client when the reactor is connected

        :param connection:
        :return:
        """
        self.print_debug("Connection successful!", True)
        self.client = connection
        self._backoff = _BACKOFF

        self.client.get_power()
        self.client.get_volume()
        self.client.get_mute()
        self.client.get_source()

        self.close_settings()

        self.root.ids.power.disabled = False
        self.root.ids.main.disabled = False

    def on_connection_failed(self, connector: twisted.internet.tcp.Connector, reason: twisted.python.failure.Failure
                             ) -> None:
        if self.connector is connector:
            logger.debug(f"Connection failed: {reason}")
            self.print_debug("Connection to receiver failed!")
            self.client = None
            # TODO: open error popup?
            self.root.ids.power.disabled = True
            self.root.ids.main.disabled = True
            self.open_settings()

        self._reconnect()

    def on_connection_lost(self, connector: twisted.internet.tcp.Connector, reason: twisted.python.failure.Failure
                           ) -> None:
        if self.connector is connector:
            logger.debug(f"Connection lost: {reason}")
            self.print_debug("Connection to receiver lost!")
            self.client = None
            self.root.ids.power.disabled = True
            self.root.ids.main.disabled = True

        self._reconnect()

    def _reconnect(self) -> None:
        """Try to reconnect with exponential backoff"""
        self._backoff = self._backoff * 2
        self.print_debug(f"Trying to reconnect in {self._backoff} seconds.", True)
        kivy.clock.Clock.schedule_once(self._connect, self._backoff)

    @kivy.clock.mainthread
    def show(self, window: kivy.core.window.Window = None) -> None:
        if window is None:
            window = self.root_window
        window.restore()
        window.show()
        window.raise_window()
        self.hidden = False

    @kivy.clock.mainthread
    def hide(self, window: kivy.core.window.Window = None) -> None:
        if window is None:
            window = self.root_window
        window.hide()
        self.hidden = True

    def hide_on_close(self, window: kivy.core.window.Window, source: str = None) -> True:
        logger.debug(f"Hide from {source}")
        self.hide(window)
        return True  # Keeps the application alive instead of stopping

    def enable_keyboard_shortcuts(self) -> None:
        kivy.core.window.Window.bind(on_keyboard=self.on_keyboard)

    def disable_keyboard_shortcuts(self) -> None:
        kivy.core.window.Window.unbind(on_keyboard=self.on_keyboard)

    def on_keyboard(self, _: kivy.core.window.Window,
                    key: str, scancode: int = None, codepoint: str = None, modifier: str = None, **__) -> None:
        """
        Handle keyboard shortcuts
        """
        logger.debug(f"key: {key}, scancode: {scancode}, codepoint: {codepoint}, modifier: {modifier}")
        if codepoint == 'm':
            if not self.root.ids.volume_mute.disabled:
                self.root.ids.volume_mute.trigger_action()
        if scancode == 82:  # Up
            if not self.root.ids.volume_plus.disabled:
                self.root.ids.volume_plus.trigger_action()
        if scancode == 81:  # Down
            if not self.root.ids.volume_minus.disabled:
                self.root.ids.volume_minus.trigger_action()

    def logo_pressed(self, _: kivy.uix.widget.Widget) -> None:
        self.root.small = not self.root.small
        if self.root.small:
            kivy.core.window.Window.size = (WIDTH, SMALL_HEIGHT)
        else:
            kivy.core.window.Window.size = (WIDTH, HEIGHT)

    def update_power(self, status: bool = True) -> None:
        if status:
            self.root.ids.power.state = 'down'
        else:
            self.root.ids.power.state = 'normal'

    def power_pressed(self, instance: kivy.uix.widget.Widget) -> None:
        power = not bool(instance.state == 'normal')
        self.client.set_power(power)

    def update_volume(self, text: str = "", ref_level: int = None) -> None:
        # If we get no text, retrieve the currently displayed one
        if text == "":
            # We don't need to update the volume display if no text is passed
            text = self.root.ids.volume_display.text
        else:
            self.root.ids.volume_display.text = text

            # Disable minus button on boundaries
            # Plus button is handled by update_max_volume()
            if text == "---.-dB":
                self.root.ids.volume_minus.disabled = True
            else:
                self.root.ids.volume_minus.disabled = False

            # Update volume presets
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

    def update_max_volume(self, text: str = ""):
        if text:
            self.maximum_volume = text

        # Disable plus button on boundaries
        # Minus button is handled by update_volume
        if self.root.ids.volume_display.text == self.maximum_volume:
            self.root.ids.volume_plus.disabled = True
        else:
            self.root.ids.volume_plus.disabled = False

    def _compute_spl_text(self, text: str = "", ref_level: int = -18) -> (str, str):
        # FIXME: Handle Absolute mode
        # Relative mode computation
        volume = float('-inf') if text == '---.-dB' else float(text.replace(' ', '')[:-2])  # Strip "dB"
        volume_delta = volume - float(
            self.config.get('denonremote', 'reference_volume'))  # compute delta with reference volume
        if volume == float('-inf'):
            spl = volume
        else:
            spl = int(round(
                float(self.config.get('denonremote', 'reference_spl')) + volume_delta))  # apply delta to reference SPL
        # Reference mode handling
        ref_delta = ref_level - int(
            self.config.get('denonremote', 'reference_level'))  # compute delta with reference level
        spl = spl + ref_delta
        if spl == float('-inf'):
            spl = 0
        spl_text = f"{spl:d} dB SPL"  # format string with computed SPL and reference level mode
        ref_text = f"@ {ref_level:d} dBFS"
        text = (spl_text, ref_text)
        return text

    def mode_changed(self, instance: kivy.uix.widget.Widget) -> None:
        level = self._get_mode_level(instance.text)
        self.update_volume(ref_level=level)

    @staticmethod
    def _get_mode_level(instance_text: str) -> int:
        level = -18  # We default to EBU
        if instance_text == 'EBU R 128':
            level = -23  # LUFS
        elif instance_text == 'SMPTE/K-20':
            level = -20  # dBFS
        elif instance_text == 'EBU':
            level = -18  # dBFS
        elif instance_text == 'K-14':
            level = -14  # dBFS
        elif instance_text == 'K-12':
            level = -12  # dBFS
        return level

    def volume_text_changed(self, instance: kivy.uix.widget.Widget) -> None:
        # TODO: validate user input
        if len(instance.text) != 7:
            self.client.get_volume()
            return
        self.client.set_volume(instance.text)

    def volume_minus_pressed(self, _: kivy.uix.widget.Widget) -> None:
        self.client.set_volume('Down')

    def volume_plus_pressed(self, _: kivy.uix.widget.Widget) -> None:
        self.client.set_volume('Up')

    def volume_mute_pressed(self, instance: kivy.uix.widget.Widget) -> None:
        mute = bool(instance.state == 'down')
        # Stay down. Updated on message received
        self.root.ids.volume_mute.state = 'down'
        self.client.set_mute(mute)

    def set_volume_mute(self, status: bool = False) -> None:
        if status:
            self.root.ids.volume_mute.state = 'down'
            self.root.ids.volume_display.foreground_color = [.3, .3, .3, 1]
            self.root.ids.power.blink(True)
        else:
            self.root.ids.volume_mute.state = 'normal'
            self.root.ids.volume_display.foreground_color = [.85, .85, .85, 1]
            self.root.ids.power.blink(False)

    def vol_preset_1_pressed(self, instance: kivy.uix.widget.Widget) -> None:
        self.client.set_volume(self.config.get('denonremote', 'vol_preset_1'))
        instance.state = 'down'  # Disallow depressing the button manually

    def vol_preset_2_pressed(self, instance: kivy.uix.widget.Widget) -> None:
        self.client.set_volume(self.config.get('denonremote', 'vol_preset_2'))
        instance.state = 'down'

    def vol_preset_3_pressed(self, instance: kivy.uix.widget.Widget) -> None:
        self.client.set_volume(self.config.get('denonremote', 'vol_preset_3'))
        instance.state = 'down'

    def vol_preset_4_pressed(self, instance: kivy.uix.widget.Widget) -> None:
        self.client.set_volume(self.config.get('denonremote', 'vol_preset_4'))
        instance.state = 'down'

    def set_sources(self, source: str = None) -> None:
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
        if source in self.config.get('denonremote', 'fav_src_4_code'):
            self.root.ids.fav_src_4.state = 'down'
        else:
            self.root.ids.fav_src_4.state = 'normal'
        if source in self.config.get('denonremote', 'fav_src_5_code'):
            self.root.ids.fav_src_5.state = 'down'
        else:
            self.root.ids.fav_src_5.state = 'normal'
        if source in self.config.get('denonremote', 'fav_src_6_code'):
            self.root.ids.fav_src_6.state = 'down'
        else:
            self.root.ids.fav_src_6.state = 'normal'

    def fav_src_1_pressed(self, instance: kivy.uix.widget.Widget) -> None:
        self.client.set_source(self.config.get('denonremote', 'fav_src_1_code'))
        instance.state = 'down'  # Disallow depressing the button manually

    def fav_src_2_pressed(self, instance: kivy.uix.widget.Widget) -> None:
        self.client.set_source(self.config.get('denonremote', 'fav_src_2_code'))
        instance.state = 'down'

    def fav_src_3_pressed(self, instance: kivy.uix.widget.Widget) -> None:
        self.client.set_source(self.config.get('denonremote', 'fav_src_3_code'))
        instance.state = 'down'

    def fav_src_4_pressed(self, instance: kivy.uix.widget.Widget) -> None:
        self.client.set_source(self.config.get('denonremote', 'fav_src_4_code'))
        instance.state = 'down'

    def fav_src_5_pressed(self, instance: kivy.uix.widget.Widget) -> None:
        self.client.set_source(self.config.get('denonremote', 'fav_src_5_code'))
        instance.state = 'down'

    def fav_src_6_pressed(self, instance: kivy.uix.widget.Widget) -> None:
        self.client.set_source(self.config.get('denonremote', 'fav_src_6_code'))
        instance.state = 'down'

    def print_debug(self, msg: str, echo_to_logger: bool = False) -> None:
        if echo_to_logger:
            logger.debug(msg)
        self.root.ids.debug_messages.text += f"{msg}\n"
