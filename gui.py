# -*- coding: utf-8 -*-
# fix for pyinstaller packages app to avoid ReactorAlreadyInstalledError
# See: https://github.com/kivy/kivy/issues/4182
# See: https://github.com/pyinstaller/pyinstaller/issues/3390
import sys

import kivy
from kivy import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton

from config import RECEIVER_IP, RECEIVER_PORT, VOL_PRESET_1, VOL_PRESET_2, VOL_PRESET_3, FAV_SRC_1_LABEL, \
    FAV_SRC_2_LABEL, FAV_SRC_3_LABEL, FAV_SRC_1_CODE, FAV_SRC_2_CODE, FAV_SRC_3_CODE, DEBUG

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
    volume = None
    volume_plus = None
    volume_minus = None
    vol_preset_1 = None
    vol_preset_2 = None
    vol_preset_3 = None
    mute = None
    fav_src_1 = None
    fav_src_2 = None
    fav_src_3 = None

    def build(self):
        self.title = "Denon Remote"
        root = self.setup_gui()
        self.connect_to_receiver()
        return root

    def setup_gui(self):
        # TODO: switch to kv lang?

        layout = BoxLayout(orientation='horizontal', padding=10)

        content = BoxLayout(orientation='vertical', padding=10)

        power_layout = BoxLayout(orientation='horizontal')
        power_label = Label(text="Power")
        self.power = CheckBox(active=True)
        power_layout.add_widget(power_label)
        power_layout.add_widget(self.power)

        content.add_widget(power_layout)

        volume_layout = BoxLayout(orientation='horizontal')
        volume_label = Label(text="Volume")
        self.volume = TextInput(text="Unknown", font_size=40, halign='center', multiline=False,
                                background_color=[0, 0, 0, 1], foreground_color=[1, 1, 1, 1], padding=0)
        volume_layout.add_widget(volume_label)
        volume_display_layout = BoxLayout(orientation='vertical')
        volume_display_layout.add_widget(self.volume)
        volume_keys_layout = BoxLayout(orientation='horizontal')
        self.volume_plus = Button(text="+")
        self.volume_minus = Button(text="-")
        volume_keys_layout.add_widget(self.volume_minus)
        volume_keys_layout.add_widget(self.volume_plus)
        volume_display_layout.add_widget(volume_keys_layout)
        volume_presets_layout = BoxLayout(orientation='horizontal')
        self.vol_preset_1 = ToggleButton(text=VOL_PRESET_1, group='vol_preset')
        self.vol_preset_2 = ToggleButton(text=VOL_PRESET_2, group='vol_preset')
        self.vol_preset_3 = ToggleButton(text=VOL_PRESET_3, group='vol_preset')
        volume_presets_layout.add_widget(self.vol_preset_1)
        volume_presets_layout.add_widget(self.vol_preset_2)
        volume_presets_layout.add_widget(self.vol_preset_3)
        volume_display_layout.add_widget(volume_presets_layout)

        volume_layout.add_widget(volume_display_layout)

        content.add_widget(volume_layout)

        mute_layout = BoxLayout(orientation='horizontal')
        mute_layout.add_widget(Label(text="Mute"))
        self.mute = CheckBox(active=False)
        mute_layout.add_widget(self.mute)

        content.add_widget(mute_layout)

        source_layout = BoxLayout(orientation='horizontal')
        source_layout.add_widget(Label(text="Sources"))
        sources_list_layout = BoxLayout(orientation='vertical')
        self.fav_src_1 = ToggleButton(text=FAV_SRC_1_LABEL, group='sources')
        self.fav_src_2 = ToggleButton(text=FAV_SRC_2_LABEL, group='sources')
        self.fav_src_3 = ToggleButton(text=FAV_SRC_3_LABEL, group='sources')
        sources_list_layout.add_widget(self.fav_src_1)
        sources_list_layout.add_widget(self.fav_src_2)
        sources_list_layout.add_widget(self.fav_src_3)
        source_layout.add_widget(sources_list_layout)
        content.add_widget(source_layout)

        layout.add_widget(content)

        self.debug_messages = TextInput(background_color=[0, 0, 0, 1], foreground_color=[0, 1, 0, 1])
        if DEBUG:
            layout.add_widget(self.debug_messages)
        return layout

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

        self.power.bind(active=self.power_callback)
        self.volume.bind(on_text_validate=self.volume_callback)
        self.volume_minus.bind(on_press=self.volume_minus_callback)
        self.volume_plus.bind(on_press=self.volume_plus_callback)
        self.vol_preset_1.bind(on_press=self.vol_preset_1_callback)
        self.vol_preset_2.bind(on_press=self.vol_preset_2_callback)
        self.vol_preset_3.bind(on_press=self.vol_preset_3_callback)
        self.mute.bind(active=self.mute_callback)
        self.fav_src_1.bind(on_press=self.fav_src_1_callback)
        self.fav_src_2.bind(on_press=self.fav_src_2_callback)
        self.fav_src_3.bind(on_press=self.fav_src_3_callback)

    def print_message(self, msg):
        self.debug_messages.text += "{}\n".format(msg)

    def set_power_button(self, status=True):
        if status:
            self.power.active = True
        else:
            self.power.active = False

    def power_callback(self, instance, value):
        self.connection.set_power(value)

    def set_volume(self, text=""):
        self.volume.text = text
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

    def volume_callback(self, instance, value=''):
        # FIXME: value is useless
        # TODO: confirmation?
        self.connection.set_volume(instance.text)

    def volume_minus_callback(self, instance):
        self.connection.set_volume('Down')

    def volume_plus_callback(self, instance):
        self.connection.set_volume('Up')

    def vol_preset_1_callback(self, instance):
        self.connection.set_volume(VOL_PRESET_1)
        instance.state = 'down'  # Disallow depressing the button manually

    def vol_preset_2_callback(self, instance):
        self.connection.set_volume(VOL_PRESET_2)
        instance.state = 'down'

    def vol_preset_3_callback(self, instance):
        self.connection.set_volume(VOL_PRESET_3)
        instance.state = 'down'

    def set_mute_button(self, status=True):
        if status:
            self.mute.active = True
        else:
            self.mute.active = False

    def mute_callback(self, instance, value):
        self.connection.set_mute(value)

    def set_source(self, source=None):
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
