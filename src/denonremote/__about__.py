# This Python file uses the following encoding: utf-8
#
# SPDX-FileCopyrightText: 2021-2022 Raphaël Doursenaud <rdoursenaud@free.fr>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Denon Remote project metadata.
"""

__TITLE__ = "Denon Remote"
__version__ = "0.10.0"  # https://peps.python.org/pep-0440/
try:
    from denonremote.__build__ import __build_date__
except ImportError:
    __build_date__ = "<source>"
