#!/bin/env python3
# -*- coding: utf-8 -*-

"""
Denon DN-500AV Remote

@author Raphael Doursenaud <rdoursenaud@gmail.com>
"""

TITLE = "Denon Remote"
__version__ = "0.6.0"  # FIXME: use setuptools
__BUILD_DATE__ = "<source>"  # TODO: override at build time

import argparse
import logging
import os
import sys

import PIL.Image
import pystray

logger = logging.getLogger()


# FIXME: use kivy.resources.resource_find instead
def resource_path(relative_path: str):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    else:
        base_path = os.getcwd()

    return os.path.join(base_path, relative_path)


def run_gui(systray: pystray.Icon = None):
    from gui import DenonRemoteApp
    if systray is not None:
        DenonRemoteApp().run_with_systray(systray)
    else:
        DenonRemoteApp().run()


def run_gui_from_systray():
    default_menu_item = pystray.MenuItem(TITLE, systray_clicked, default=True, visible=False)
    quit_menu_item = pystray.MenuItem('Quit', quit_systray)
    systray_menu = pystray.Menu(default_menu_item, quit_menu_item)
    systray = pystray.Icon(TITLE, menu=systray_menu)
    systray.icon = PIL.Image.open(resource_path(r'images/icon.png'))
    systray.run(setup=run_gui)


def configure(args: argparse.Namespace):
    import kivy.config

    # App specific configuration
    # FIXME: use same implementation as Kivy to avoid issues
    kivy.config.Config.read(os.path.expanduser('~/.denonremote.ini'))

    # Make sure we have our section
    kivy.config.Config.adddefaultsection('denonremote')

    # Fixed size window
    kivy.config.Config.set('graphics', 'resizable', False)

    # wm_pen and wm_touch conflicts with hidden window state. See https://github.com/kivy/kivy/issues/6428
    kivy.config.Config.remove_option('input', 'wm_pen')
    kivy.config.Config.remove_option('input', 'wm_touch')

    # Hide annoying multitouch emulation
    kivy.config.Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

    # Start hidden when using systray
    if args.no_systray:
        kivy.config.Config.set('graphics', 'window_state', 'visible')
    else:
        kivy.config.Config.set('graphics', 'window_state', 'hidden')

    if args.debug:
        kivy.config.Config.set('kivy', 'log_level', 'debug')
        kivy.config.Config.set('denonremote', 'debug', '1')
    else:
        kivy.config.Config.set('kivy', 'log_level', 'warning')
        kivy.config.Config.set('denonremote', 'debug', '0')

    kivy.config.Config.write()


def init_logging():
    global logger

    import kivy.logger
    logging.shutdown()
    logger = kivy.logger.Logger

    # Replace python logger by Kivy logger to retrieve module logs
    logging.Logger.manager.root = kivy.logger.Logger

    # Retrieve log level from config
    log_level_name = kivy.config.Config.get('kivy', 'log_level')
    log_level = kivy.logger.LOG_LEVELS[log_level_name]
    logger.setLevel(log_level)
    logging.getLogger('denon.dn500av').setLevel(log_level)  # Sync module’s logging level


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


def run(args: argparse.Namespace):
    if False:  # FIXME: implement CLI commands
        run_cli()
    elif args.no_systray:
        run_gui()
    else:
        run_gui_from_systray()


def parse_args():
    # Disable Kivy arguments handling
    os.environ["KIVY_NO_ARGS"] = "1"

    parser = argparse.ArgumentParser(prog=TITLE,
                                     description="Control Denon Professional DN-500AV surround preamplifier remotely")
    parser.add_argument('--debug', dest='debug', action='store_true', default=False,
                        help="Enable debugging output")
    parser.add_argument('--no-systray', action='store_true', help="Disable systray")
    return parser.parse_args()


if __name__ == '__main__':
    arguments = parse_args()
    configure(arguments)
    init_logging()
    run(arguments)
