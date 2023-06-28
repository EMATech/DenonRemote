[![Denon Remote Logo](https://raw.githubusercontent.com/EMATech/denonremote/main/data/assets/icon_24.png) Denon Remote](https://github.com/ematech/denonremote)
===================================================================================================

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/denonremote.svg)](https://pypi.org/project/denonremote)
[![Downloads](https://pepy.tech/badge/denonremote)](https://pepy.tech/project/denonremote)
[![PyPI - Version](https://img.shields.io/pypi/v/denonremote.svg)](https://pypi.org/project/denonremote)

Control [Denon Professional DN-500AV surround preamplifier](https://www.denonpro.com/index.php/products/view/dn-500av)
remotely.

![Screenshot](https://raw.githubusercontent.com/EMATech/denonremote/main/data/screenshots/screenshot-v0.9.0-main.png)

![Settings Screenshot](https://raw.githubusercontent.com/EMATech/denonremote/main/data/screenshots/screenshot-v0.9.0-settings.png)

### Features

#### Target hardware

- [x] Denon Professional DN-500AV (Seems to be based on the same platform as the Denon AVR-1912 and AVR-2112CI)
- [ ] More? Contributions welcome!

#### Communication

- [x] Ethernet
    - [x] Using [Twisted](https://twistedmatrix.com)
    - [x] connection status detection
    - [x] automatically try to reconnect with exponential backoff
- [ ] RS-232? also using Twisted
- [ ] General MIDI input using [Mido](https://mido.readthedocs.io/en/latest/)
    - [ ] Define control scheme.
      See: [Summary of MIDI 1.0 Messages](https://www.midi.org/specifications-old/item/table-1-summary-of-midi-message)
      , [MIDI 1.0 Control Change Messages](https://www.midi.org/specifications-old/item/table-3-control-change-messages-data-bytes-2)
        - [ ] CC7 = Master Volume
        - [ ] CC120 = Mute
        - [ ] CC? = On/Standby
        - [ ] Program Changes -> Inputs select
            - [ ] Mapping?
    - [ ] Virtual ports
        - [ ] using [loopMidi](http://www.tobias-erichsen.de/software/loopmidi.html) for Windows
        - [ ] rt-midi native for *NIX OSes
        - [ ] rtpMIDI?

#### Controls

- [x] Setup
    - [x] IP address
    - [ ] Serial port?
        - [ ] COM (Windows)
        - [ ] tty (*NIX OSes)
- [x] On/Standby
- [x] Main volume
    - [x] Get
        - [x] Relative
        - [ ] Absolute
    - [x] Set
        - [x] Relative
        - [x] Absolute
    - [x] Mute
- [x] SPL calibrated display
    - [x] EBU/SMPTE RP200: 85dB C SPL @ -18 dBFS (Equivalent to 83 dB C SPL @ -20 dBFS)
    - [x] K meter
        - [x] K-20: -20dBFS = 83dB C SPL (Same as SMPTE and EBU)
        - [x] K-14: -14dBFS = 83dB C SPL
            - [ ] Can be compensated from SMPTE/EBU levels by lowering the output volume by 6dB
        - [x] K-12: -12dBFS = 83dB C SPL
            - [ ] Can be compensated from SMPTE/EBU levels by lowering the output volume by 8dB
    - [x] EBU R 128: -23LUFS (-23dBFS) = 73dB C SPL (Debatable/unclear removed for now)
    - [x] Presets!
        - [x] Relative (-18dB, -24dB…)
        - [ ] Absolute
        - [ ] SPL calibrated
- [ ] Zone 2
- [ ] Per Channel level (Up to 7.1)
- [ ] Tone
- [ ] EQ
- [ ] Sound presets
- [ ] Input select
    - [x] Favorites
- [ ] Security
    - [ ] Panel Lock
    - [ ] IR Remote Lock
- [ ] Settings backup/restore
    - [ ] All
    - [ ] Subsystems?
- [x] Retrieve status
    - [x] Logger
    - [x] Update the GUI
- [ ] Import EQ settings
    - [ ] From [REW](https://www.roomeqwizard.com/) value file
        - [ ] Only use negative values! You can’t compensate a destructive room mode by adding energy to it.
- [ ] Full Profiles/presets?

##### GUI

- [x] Using [Kivy](https://kivy.org)
    - [ ] Keyboard shortcuts:
        - [x] M for Mute
        - [x] Up/Down Vol +/-
        - [ ] Left/Right VolPreset +/-
        - [ ] PgUp/PgDwn SrcPreset +/-
- [x] Systray/Taskbar support using [pystray](https://pypi.org/project/pystray/)
- [x] Only one instance is allowed (Microsoft Windows only)
- [X] Option to make window stay always on top (Microsoft Windows only)
- [x] Touch doesn't activate the window and doesn't steal focus (Microsoft Windows only)
- [x] Trigger events without having to activate the window first (Microsoft Windows only)
- [ ] Draw it on the first touch enabled display if available instead of the main one

##### Windows executable

- [ ] Handle shutdown to power off the device
- [x] Generate icon with [IconMaker](https://github.com/Inedo/iconmaker)
- [x] [PyInstaller](https://www.pyinstaller.org) (Fairly stable for Microsoft Windows)
    - [x] [UPX](https://upx.github.io/) support
    - How to build:
        - Review [denonremote.spec](denonremote.spec)
        - Use `hatch build; hatch run build:pyinstaller`
- [x] [Nuitka](https://nuitka.net) (Alpha support for Microsoft Windows)
    - Use `hatch build; hatch run build:nuitka`
- [ ] [PyOxidiser](https://github.com/indygreg/PyOxidizer)
- [ ] [cx-Freeze](https://pypi.org/project/cx-Freeze/) for multiplatform support?
- [ ] VST plugin? (Not required if MIDI input is implemented but would be neat to have in the monitoring section of a
  DAW)
    - [ ] See [PyVST](https://pypi.org/project/pyvst/)

#### Mobile

- [ ] Autonomous mobile app? Kivy enables that!
    - [ ] Android
    - [ ] iOS/iPadOS

#### Proxy/background service?

The receiver only allows 1 active connection. A dispatcher proxy could allow multiple simultaneous remotes (Desktop and
mobile).

### Other opportunities

Open ports:

- 23/tcp (TELNET): BridgeCo AG Telnet server  
  AVR serial protocol used here
- 80/tcp (HTTP): GoAhead WebServer  
  Web control (index.asp) Shows nothing.  
  Most of the useful code is commented!  
  CSS loading at "css/mainMenu.css" times out.  
  Main control is available at "MainZone/index.html"!
- 443/tcp (HTTPS):  
  ERR_SSL_PROTOCOL_ERROR in Google Chrome  
  SSL_ERROR_EXTRACT_PUBLIC_KEY_FAILURE in Mozilla Firefox
- 1026/tcp (RTSP): Apple AirTunes rtspd 103.2
- 6666/tcp: ?
- 8080/tcp (HTTP): AV receiver http config

### Similar projects

Android

- [AVR-Remote](https://github.com/pskiwi/avr-remote)

JavaScript:

- https://github.com/phillipsnick/denon-avr
- https://github.com/murderbeard/com.moz.denon
- https://github.com/jtangelder/denon-remote

PHP

- https://github.com/Wolbolar/IPSymconDenon (IP Symcon automation)

Python:

- https://github.com/jeroenvds/denonremote (XBMC plugin)
- https://github.com/Tom360V/DenonAvr (Similar objectives?)
- https://github.com/toebsen/python-denonavr (HTTP RESTful server)
- https://github.com/MrJavaWolf/DenonPhoneController (Landline phone controller)
- https://github.com/troykelly/python-denon-avr-serial-over-ip (Library)
- https://github.com/auchter/denonavr_serial (Library)
- https://github.com/jphutchins/pyavreceiver (Nice library)
- https://github.com/frawau/aiomadeavr (Library)
- https://github.com/scarface-4711/denonavr (Uses the HTTP/XML interface. Library)

Legal notice
------------

### License

![GPLv3](https://raw.githubusercontent.com/EMATech/denonremote/main/data/assets/sources/gplv3-or-later.svg)

Author: ©2021-2022 Raphaël Doursenaud.

This software is released under the terms of the GNU General Public License, version 3.0 or later (GPL-3.0-or-later).

See [LICENSE](LICENSE).

Logo and icons released under the
[Creative Commons Attribution-Share Alike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/).

### Dependencies & License Acknowledgment

- [Python](https://python.org) v3.10  
  Copyright © 2001-2022 Python Software Foundation.  
  Used under the terms of the PSF License Agreement.
- [Kivy](https://kivy.org/)  
  Copyright 2010-2022, The Kivy Authors.  
  Used under the terms of the MIT license.  
  Uses:
    - [docutils](https://docutils.sourceforge.io/COPYING.html)
    - [pygments](https://github.com/pygments/pygments/blob/master/LICENSE)
    - [sdl2](https://www.libsdl.org/license.php)
    - [glew](https://glew.sourceforge.net/glew.txt)
    - [pywin32](https://pypi.org/project/pywin32/)
    - [zlib](https://github.com/madler/zlib/blob/master/README)
- [Twisted](https://twisted.org/)  
  Copyright (c) 2001-2022 Twisted Matrix Laboratories.  
  Used under the terms of the MIT license.
- [PyInstaller](https://pyinstaller.org)  
  Copyright (c) 2010-2022, PyInstaller Development Team.  
  Copyright (c) 2005-2009, Giovanni Bajo.  
  Based on previous work under copyright (c) 2002 McMillan Enterprises, Inc.  
  Used under the terms of the GNU General Public License version 2.0.
    - includes [cpython](https://hg.python.org/cpython/file/tip/Tools/msi/exe/crtlicense.txt)

#### Fonts

- [Free Serif](https://www.gnu.org/software/freefont/)  
  Copyright © 2022 Free Software Foundation, Inc.  
  Used under the terms of the GNU General Public License version 3.0.
- [Roboto Mono](https://github.com/googlefonts/RobotoMono)  
  Copyright (c) 2015 The Roboto Mono Project Authors.  
  Used under the terms of the Apache License, Version 2.0.
- [Unicode Power Symbol](https://unicodepowersymbol.com/)  
  Copyright (c) 2013 Joe Loughry.  
  Used under the terms of the MIT license.

#### Logo and icons

Own work based upon:

- [Denon Professional DN-500AV Front](https://www.denonpro.com/index.php/products/view/dn-500av#tab-images)  
  Marketing material from Denon Professional.  
  Copyright 2012-2022 inMusic Brands, Inc.

### Trademarks

- [Denon](https://www.denon.com) is a trademark of Sound United, LLC and Affiliates.
- [Denon Professional](https://www.denonpro.com) is a trademark of inMusic Brands, Inc.

#### Other

Other trademarks are property of their respective owners and used fairly for descriptive and nominative purposes only.
