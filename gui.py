# -*- coding: utf-8 -*-

import platform
import sys

import kivy
from kivy import Logger, Config

Config.set('graphics', 'resizable', False)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton

from config import RECEIVER_IP, RECEIVER_PORT, VOL_PRESET_1, VOL_PRESET_2, VOL_PRESET_3, FAV_SRC_1_LABEL, \
    FAV_SRC_2_LABEL, FAV_SRC_3_LABEL, FAV_SRC_1_CODE, FAV_SRC_2_CODE, FAV_SRC_3_CODE, DEBUG, BUILD_DATE

# fix for pyinstaller packages app to avoid ReactorAlreadyInstalledError
# See: https://github.com/kivy/kivy/issues/4182
# See: https://github.com/pyinstaller/pyinstaller/issues/3390
if 'twisted.internet.reactor' in sys.modules:
    del sys.modules['twisted.internet.reactor']

# install twisted reactor
from kivy.support import install_twisted_reactor

install_twisted_reactor()

from denon.communication import DenonClientGUIFactory

kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.label import Label
from twisted.internet import reactor

logging = Logger


class DenonRemoteApp(App):
    connection = None
    debug_messages = None
    power = None
    volume_display = None
    volume_plus = None
    volume_minus = None
    vol_preset_1 = None
    vol_preset_2 = None
    vol_preset_3 = None
    volume_mute = None
    fav_src_1 = None
    fav_src_2 = None
    fav_src_3 = None

    def build(self):
        self.title = "Denon Remote"
        # TODO: self.icon = ''
        root = self.setup_gui()
        self.connect_to_receiver()
        return root

    def setup_gui(self):
        # TODO: switch to kv lang?

        root = FloatLayout()

        denon_image = Image(source='assets/DN-500AV.png')
        denon_image.size = (0, 50)
        denon_image.size_hint = (.3, None)
        denon_image.pos_hint = {'top': .96, 'left': .99}
        root.add_widget(denon_image)

        name_label = Label(text="DENON REMOTE", font_size=40, bold=True)
        name_label.size = (200, 50)
        name_label.size_hint = (1, None)
        name_label.pos_hint = {'top': .96}
        name_label.color = [.75, .75, .75, 1]

        root.add_widget(name_label)

        content = BoxLayout(orientation='vertical', spacing=15)
        content.size_hint = (1, .75)
        content.pos = (0, 65)
        content.pos_hint = {'top': .85}

        self.power = ToggleButton(text="⏻", font_name='Unicode_IEC_symbol', font_size=50)
        self.power.size = (80, 72)
        self.power.size_hint = (None, None)
        self.power.pos_hint = {'top': .983, 'right': .87}
        self.power.background_color = [.3, .3, .3, 1]
        root.add_widget(self.power)

        volume_section = BoxLayout(orientation='vertical')
        self.volume_display = TextInput(text="---.-dB", font_name="RobotoMono-Regular", font_size=36,
                                        halign='center', multiline=False)
        self.volume_display.size = (200, 60)
        self.volume_display.size_hint = (1, None)
        self.volume_display.foreground_color = [.85, .85, .85, 1]
        self.volume_display.background_color = [.1, .1, .1, 1]
        volume_section.add_widget(self.volume_display)
        volume_keys_layout = BoxLayout(orientation='horizontal')
        self.volume_plus = Button(text="+")
        self.volume_minus = Button(text="-")
        volume_keys_layout.add_widget(self.volume_minus)
        volume_keys_layout.add_widget(self.volume_plus)
        volume_section.add_widget(volume_keys_layout)
        self.volume_mute = ToggleButton(text="Mute", group='mute')
        volume_section.add_widget(self.volume_mute)
        volume_presets_layout = BoxLayout(orientation='horizontal')
        self.vol_preset_1 = ToggleButton(text=VOL_PRESET_1, group='vol_preset')
        self.vol_preset_2 = ToggleButton(text=VOL_PRESET_2, group='vol_preset')
        self.vol_preset_3 = ToggleButton(text=VOL_PRESET_3, group='vol_preset')
        volume_presets_layout.add_widget(self.vol_preset_1)
        volume_presets_layout.add_widget(self.vol_preset_2)
        volume_presets_layout.add_widget(self.vol_preset_3)
        volume_section.add_widget(volume_presets_layout)
        content.add_widget(volume_section)

        sources_section = BoxLayout(orientation='vertical')
        self.fav_src_1 = ToggleButton(text=FAV_SRC_1_LABEL, group='sources')
        self.fav_src_2 = ToggleButton(text=FAV_SRC_2_LABEL, group='sources')
        self.fav_src_3 = ToggleButton(text=FAV_SRC_3_LABEL, group='sources')
        sources_section.add_widget(self.fav_src_1)
        sources_section.add_widget(self.fav_src_2)
        sources_section.add_widget(self.fav_src_3)
        content.add_widget(sources_section)

        root.add_widget(content)

        brand_layout = BoxLayout(orientation='vertical')
        brand_label = Label(text="EMA Tech.")
        os_name = platform.system()
        build_date = BUILD_DATE
        version_label = Label(text="pre-release %s, (Built on %s)" % (os_name, build_date), font_size=10)
        brand_layout.add_widget(brand_label)
        brand_layout.add_widget(version_label)
        brand_layout.size = (200, 65)
        brand_layout.size_hint = (1, None)
        brand_layout.pos_hint = {'bottom': 1}

        root.add_widget(brand_layout)

        self.debug_messages = TextInput(background_color=[0, 0, 0, 1], foreground_color=[0, 1, 0, 1])
        self.debug_messages.size = (200, 65)
        self.debug_messages.size_hint = (1, None)
        if DEBUG:
            root.add_widget(self.debug_messages)

        return root

    def connect_to_receiver(self):
        self.print_message('Connection to ' + RECEIVER_IP + '...\n')
        reactor.connectTCP(RECEIVER_IP, RECEIVER_PORT, DenonClientGUIFactory(self))

    def on_connection(self, connection):
        self.print_message('... successful!\n')
        self.connection = connection

        self.connection.get_power()
        self.connection.get_volume()
        self.connection.get_mute()
        self.connection.get_source()

        self.power.bind(on_press=self.power_callback)
        self.volume_display.bind(on_text_validate=self.volume_callback)
        self.volume_minus.bind(on_press=self.volume_minus_callback)
        self.volume_plus.bind(on_press=self.volume_plus_callback)
        self.volume_mute.bind(on_press=self.volume_mute_callback)
        self.vol_preset_1.bind(on_press=self.vol_preset_1_callback)
        self.vol_preset_2.bind(on_press=self.vol_preset_2_callback)
        self.vol_preset_3.bind(on_press=self.vol_preset_3_callback)
        self.fav_src_1.bind(on_press=self.fav_src_1_callback)
        self.fav_src_2.bind(on_press=self.fav_src_2_callback)
        self.fav_src_3.bind(on_press=self.fav_src_3_callback)

    def print_message(self, msg):
        self.debug_messages.text += "{}\n".format(msg)

    def update_power(self, status=True):
        if status:
            self.power.state = 'down'
            self.power.color = [.1, .8, .1, 1]  # Green
        else:
            self.power.state = 'normal'
            self.power.color = [.8, .1, .1, 1]  # Red

    def power_callback(self, instance):
        power = False if instance.state == 'normal' else True
        self.connection.set_power(power)

    def update_volume(self, text=""):
        self.volume_display.text = text
        if text in VOL_PRESET_1:
            self.vol_preset_1.state = 'down'
        else:
            self.vol_preset_1.state = 'normal'
        if text in VOL_PRESET_2:
            self.vol_preset_2.state = 'down'
        else:
            self.vol_preset_2.state = 'normal'
        if text in VOL_PRESET_3:
            self.vol_preset_3.state = 'down'
        else:
            self.vol_preset_3.state = 'normal'

    def volume_callback(self, instance):
        # TODO: validate user input
        if len(instance.text) != 7:
            self.connection.get_volume()
            return
        self.connection.set_volume(instance.text)

    def volume_minus_callback(self, instance):
        self.connection.set_volume('Down')

    def volume_plus_callback(self, instance):
        self.connection.set_volume('Up')

    def volume_mute_callback(self, instance):
        mute = True if instance.state == 'down' else False
        # Stay down. Updated on message received
        self.volume_mute.state = 'down'
        self.connection.set_mute(mute)

    def update_volume_mute(self, status=False):
        if status:
            self.volume_mute.state = 'down'
            self.volume_display.foreground_color = [.3, .3, .3, 1]
        else:
            self.volume_mute.state = 'normal'
            self.volume_display.foreground_color = [.85, .85, .85, 1]

    def vol_preset_1_callback(self, instance):
        self.connection.set_volume(VOL_PRESET_1)
        instance.state = 'down'  # Disallow depressing the button manually

    def vol_preset_2_callback(self, instance):
        self.connection.set_volume(VOL_PRESET_2)
        instance.state = 'down'

    def vol_preset_3_callback(self, instance):
        self.connection.set_volume(VOL_PRESET_3)
        instance.state = 'down'

    def update_source(self, source=None):
        if source in FAV_SRC_1_CODE:
            self.fav_src_1.state = 'down'
        else:
            self.fav_src_1.state = 'normal'
        if source in FAV_SRC_2_CODE:
            self.fav_src_2.state = 'down'
        else:
            self.fav_src_2.state = 'normal'
        if source in FAV_SRC_3_CODE:
            self.fav_src_3.state = 'down'
        else:
            self.fav_src_3.state = 'normal'

        # TODO: display other sources

    def fav_src_1_callback(self, instance):
        self.connection.set_source(FAV_SRC_1_CODE)
        instance.state = 'down'  # Disallow depressing the button manually

    def fav_src_2_callback(self, instance):
        self.connection.set_source(FAV_SRC_2_CODE)
        instance.state = 'down'

    def fav_src_3_callback(self, instance):
        self.connection.set_source(FAV_SRC_3_CODE)
        instance.state = 'down'
