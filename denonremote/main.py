#!/bin/env python3
# -*- coding: utf-8 -*-

"""
Denon DN-500AV Remote

@author Raphael Doursenaud <rdoursenaud@gmail.com>
"""

__author__ = 'Raphaël Doursenaud <rdoursenaud@gmail.com>'

__version__ = '0.4.0'  # FIXME: use setuptools

import logging

import PIL.Image
import pystray

from config import DEBUG, GUI

logger = logging.getLogger()


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    import os, sys
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    else:
        base_path = os.getcwd()

    return os.path.join(base_path, relative_path)


def init_logging():
    global logger

    if not GUI:
        if DEBUG:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
            logging.getLogger('denon.dn500av').setLevel(logging.WARNING)  # Silence module’s logging
    else:
        import kivy.logger
        logger = kivy.logger.Logger
        logging.Logger.manager.root = kivy.logger.Logger  # Hack to retrieve logs from modules using standard logging into Kivy
        if DEBUG:
            logger.setLevel(kivy.logger.LOG_LEVELS['debug'])
        else:
            logger.setLevel(kivy.logger.LOG_LEVELS['info'])
            logging.getLogger('denon.dn500av').setLevel(logging.WARNING)  # Silence module’s logging


def run_from_systray():
    default_menu_item = pystray.MenuItem('Denon Remote', systray_clicked, default=True, visible=False)
    quit_menu_item = pystray.MenuItem('Quit', quit_systray)
    systray_menu = pystray.Menu(default_menu_item, quit_menu_item)
    systray = pystray.Icon('Denon Remote', menu=systray_menu)
    systray.icon = PIL.Image.open(resource_path(r'images/icon.png'))
    systray.run(setup=run_gui)


def run_gui(systray):
    import kivy.config
    kivy.config.Config.set('kivy', 'window_icon', 'images/icon.png')
    # Fixed size window
    kivy.config.Config.set('graphics', 'resizable', False)
    # Start hidden
    kivy.config.Config.set('graphics', 'window_state', 'hidden')
    # wm_pen and wm_touch conflicts with hidden window state. See https://github.com/kivy/kivy/issues/6428
    kivy.config.Config.remove_option('input', 'wm_pen')
    kivy.config.Config.remove_option('input', 'wm_touch')
    kivy.config.Config.write()

    from gui import DenonRemoteApp
    DenonRemoteApp().run_with_systray(systray)


def systray_clicked(icon: pystray.Icon, menu: pystray.MenuItem):
    import kivy.app
    app = kivy.app.App.get_running_app()
    if app.hidden:
        app.show()
    else:
        app.hide()


def quit_systray(icon: pystray.Icon, menu: pystray.MenuItem):
    import kivy.app
    kivy.app.App.get_running_app().stop()
    icon.stop()


def run_cli():
    from cli import DenonRemoteApp
    DenonRemoteApp().run()


def run():
    # FIXME: autodetect when running from CLI
    if GUI:
        run_from_systray()
    else:
        run_cli()


if __name__ == '__main__':
    init_logging()
    run()
