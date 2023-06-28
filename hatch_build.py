# This Python file uses the following encoding: utf-8
#
# SPDX-FileCopyrightText: 2023 Raphaël Doursenaud <rdoursenaud@free.fr>
#
# SPDX-License-Identifier: GPL-3.0-or-later
import os
from datetime import datetime
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

BUILD_FILE = 'src/denonremote/__build__.py'


class CustomBuildHook(BuildHookInterface):

    def _get_build_file(self):
        return os.path.join(self.root, BUILD_FILE)

    def clean(self, versions: list[str]) -> None:
        # Cleanup the build file
        try:
            os.remove(self._get_build_file())
        except FileNotFoundError:
            pass

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        print(version)
        # Create the build
        __build_date__ = datetime.now().isoformat()
        build_file = self._get_build_file()
        with open(build_file, 'w') as f:
            f.write(f'__build_date__ = "{__build_date__}"\r')
        # __build__.py is in .gitignore. We must force its inclusion
        self.build_config.force_include[build_file] = BUILD_FILE
        print(self.build_config.force_include)
