# This Python file uses the following encoding: utf-8
#
# SPDX-FileCopyrightText: 2021-2022 Raphaël Doursenaud <rdoursenaud@free.fr>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Denon DN-500AV Remote

@author Raphael Doursenaud <rdoursenaud@gmail.com>
"""

import argparse
import logging
import os
import sys

import PIL.Image
import pystray
import win32api
import win32event
from winerror import ERROR_ALREADY_EXISTS

from denonremote.__about__ import __TITLE__

logger = logging.getLogger()


def configure(args: argparse.Namespace) -> None:
    import kivy.config

    # App specific configuration
    # FIXME: use same implementation as Kivy to avoid issues
    kivy.config.Config.read(os.path.expanduser('~/.denonremote.ini'))

    # Make sure we have our section
    kivy.config.Config.adddefaultsection('denonremote')

    # Fixed size window
    kivy.config.Config.set('graphics', 'resizable', '0')

    # No titlebar
    kivy.config.Config.set('graphics', 'borderless', '1')

    # wm_pen and wm_touch conflicts with hidden window state. See https://github.com/kivy/kivy/issues/6428
    kivy.config.Config.remove_option('input', 'wm_pen')
    kivy.config.Config.remove_option('input', 'wm_touch')

    # Hide annoying multitouch emulation
    kivy.config.Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

    # Start hidden when using systray
    if args.no_systray:
        kivy.config.Config.set('graphics', 'window_state', 'visible')
    else:
        # FIXME: should be `hidden` but can't because of https://github.com/kivy/kivy/issues/7874
        kivy.config.Config.set('graphics', 'window_state', 'visible')

    if args.debug:
        kivy.config.Config.set('kivy', 'log_level', 'debug')
        kivy.config.Config.set('denonremote', 'debug', '1')
    else:
        kivy.config.Config.set('kivy', 'log_level', 'warning')
        kivy.config.Config.set('denonremote', 'debug', '0')

    try:
        kivy.config.Config.write()
    except PermissionError:
        logger.error("Unable to save config!")


def init_logging() -> None:
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


def run_cli() -> None:
    from denonremote.cli import DenonRemoteApp
    DenonRemoteApp().run()


def run_gui(systray: pystray.Icon = None) -> None:
    import denonremote.gui
    if systray is not None:
        denonremote.gui.DenonRemoteApp().run_with_systray(systray)
    else:
        denonremote.gui.DenonRemoteApp().run()


def systray_clicked(_: pystray.Icon, __: pystray.MenuItem) -> None:
    import kivy.app
    app = kivy.app.App.get_running_app()
    if app.hidden:
        app.show()
    else:
        app.hide()


def systray_settings(_: pystray.Icon, __: pystray.MenuItem) -> None:
    import kivy.app
    app = kivy.app.App.get_running_app()
    if app.hidden:
        app.show()

    import kivy.clock
    kivy.clock.Clock.schedule_once(kivy.app.App.get_running_app().open_settings)


def systray_quit(icon: pystray.Icon, _: pystray.MenuItem) -> None:
    import kivy.clock
    kivy.clock.Clock.schedule_once(kivy.app.App.get_running_app().stop)
    icon.stop()


# FIXME: use kivy.resources.resource_find instead
def resource_path(relative_path: str) -> os.path:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # noinspection PyProtectedMember
        base_path = sys._MEIPASS
    else:
        base_path = os.getcwd()

    return os.path.join(base_path, relative_path)


def run_gui_from_systray() -> None:
    default_menu_item = pystray.MenuItem(__TITLE__, systray_clicked, default=True, visible=True)
    settings_menu_item = pystray.MenuItem('Settings', systray_settings)
    quit_menu_item = pystray.MenuItem('Quit', systray_quit)
    systray_menu = pystray.Menu(default_menu_item, settings_menu_item, quit_menu_item)
    systray = pystray.Icon(__TITLE__, menu=systray_menu)
    systray.icon = PIL.Image.open(resource_path(r'images/icon.png'))
    systray.run(setup=run_gui)


def run(args: argparse.Namespace) -> None:
    if False:  # FIXME: implement CLI commands
        run_cli()
    elif args.no_systray:
        run_gui()
    else:
        run_gui_from_systray()


def parse_args() -> argparse.Namespace:
    # Disable Kivy arguments handling
    os.environ["KIVY_NO_ARGS"] = "1"

    parser = argparse.ArgumentParser(prog=__TITLE__,
                                     description="Control Denon Professional DN-500AV surround preamplifier remotely")
    parser.add_argument('--debug', dest='debug', action='store_true', default=False,
                        help="Enable debugging output")
    parser.add_argument('--no-systray', action='store_true', help="Disable systray")
    return parser.parse_args()


if __name__ == '__main__':
    # Make sure only one instance is running
    # FIXME: Windows only ATM.
    mutex = win32event.CreateMutex(None, False, __TITLE__)
    if ERROR_ALREADY_EXISTS == win32api.GetLastError():
        sys.exit(f"{__TITLE__} is already running")

    arguments = parse_args()
    configure(arguments)
    init_logging()
    run(arguments)
