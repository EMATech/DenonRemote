#!/bin/env python3
# -*- coding: utf-8 -*-

"""
DN-500AV Remote

@author Raphael Doursenaud <rdoursenaud@gmail.com>
"""

__author__ = 'Raphaël Doursenaud'

import logging

from config import DEBUG, GUI


def init_logging():
    if not GUI:
        if DEBUG:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
            logging.getLogger("denon.dn500av").setLevel(logging.WARNING)  # Silence module’s logging
    else:
        from kivy import Logger
        logger = Logger
        if DEBUG:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)


def run():
    # FIXME: autodetect when running from CLI
    if GUI == True:
        from gui import DenonRemoteApp
        DenonRemoteApp().run()
    else:
        from cli import DenonRemoteApp
        DenonRemoteApp().run()


if __name__ == '__main__':
    init_logging()
    run()
