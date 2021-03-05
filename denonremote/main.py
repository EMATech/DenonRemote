#!/bin/env python3
# -*- coding: utf-8 -*-

"""
Denon DN-500AV Remote

@author Raphael Doursenaud <rdoursenaud@gmail.com>
"""

__author__ = 'Raphaël Doursenaud <rdoursenaud@gmail.com>'

__version__ = '0.3.0'  # FIXME: use setuptools

import logging

from config import DEBUG, GUI

logger = logging.getLogger()


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


def run():
    # FIXME: autodetect when running from CLI
    if GUI:
        from gui import DenonRemoteApp

        # PyInstaller data support
        import os, sys
        import kivy.resources
        if hasattr(sys, '_MEIPASS'):
            kivy.resources.resource_add_path(os.path.join(sys._MEIPASS))
    else:
        from cli import DenonRemoteApp

    DenonRemoteApp().run()


if __name__ == '__main__':
    init_logging()
    run()
