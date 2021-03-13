Denon Remote
============

![Screenshot](screenshot-v0.3.0.png)

Author: Raphael Doursenaud <rdoursenaud@gmail.com>

License: [GPLv3+](LICENSE)

Language: [Python](https://python.org) 3

Dependencies:

- [Unicode Power Symbol](https://unicodepowersymbol.com/) Copyright (c) 2013 Joe Loughry licensed under MIT

### Features

#### Target hardware

- [x] Denon Professional DN-500AV (Seems based on the same platform as the Denon AVR-1912 and AVR-2112CI.)
- [ ] More? Contributions welcome!

#### Communication

- [x] Ethernet
    - [x] Using [Twisted](https://twistedmatrix.com):
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

- [ ] Setup
    - [x] IP address
    - [ ] Serial port?
        - [ ] COM (Windows)
        - [ ] tty (*NIX OSes)
- [x] On/Standby
- [x] Volume control
    - [x] Get
        - [x] Relative
        - [ ] Absolute
    - [x] Set
        - [x] Relative
        - [x] Absolute
    - [x] Mute
    - [x] Presets! (-18dB, -24dB…)
    - [ ] SPL calibrated display (SMPTE RP200: -18dBFS = 85dB C SPL)
- [ ] Input select
- [ ] Security
    - [ ] Panel Lock
    - [ ] IR Remote Lock
- [ ] Settings backup/restore
    - [ ] All
    - [ ] Subsystems?

- [x] Retrieve status
    - [x] Logger
    - [x] Update the GUI

- [ ] Profiles/presets?

- [ ] Import EQ settings
    - [ ] From [REW](https://www.roomeqwizard.com/) value file

##### GUI

- [x] Using [Kivy](https://kivy.org)
    - [ ] Keyboard shortcuts:
        - [x] M for Mute
        - [x] Up/Down Vol +/-
        - [ ] Left/Right VolPreset +/-
        - [ ] PgUp/PgDwn SrcPreset +/-
- [x] Systray/Taskbar support using [pystray](https://pypi.org/project/pystray/)

##### Windows executable

- [ ] Handle shutdown to power off the device
- [x] [PyInstaller](https://www.pyinstaller.org)
    - [x] Generate icon with [IconMaker](https://github.com/Inedo/iconmaker)
    - [x] [UPX](https://upx.github.io/) support
    - How to build:
        - Review [denonremote.spec](denonremote.spec)
        - Use `python -m PyInstaller denonremote.spec --upx-dir=c:\upx-3.96-win64`
- [ ] [cx-Freeze](https://pypi.org/project/cx-Freeze/) for multiplatform support?
- [ ] VST plugin? (Not required if MIDI input is implemented but would be neat to have in the monitoring section of a
  DAW)
    - [ ] See [PyVST](https://pypi.org/project/pyvst/)

#### Mobile

- [ ] Autonomous mobile app? Kivy enables that!
    - [ ] Android
    - [ ] iOS/iPadOS

#### Proxy?

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
- 443/tcp (HTTPS): ERR_SSL_PROTOCOL_ERROR in Google Chrome  
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
- https://github.com/Tom360V/DenonAvr (Similar objectives?
- https://github.com/toebsen/python-denonavr (HTTP RESTful server)
- https://github.com/MrJavaWolf/DenonPhoneController (Landline phone controller)
- https://github.com/troykelly/python-denon-avr-serial-over-ip (Library)
- https://github.com/auchter/denonavr_serial (Library)
- https://github.com/jphutchins/pyavreceiver (Nice library)
- https://github.com/frawau/aiomadeavr (Library)
- https://github.com/scarface-4711/denonavr (Uses the HTTP/XML interface. Library)
