Denon Remote
============

Author: Raphael Doursenaud <rdoursenaud@gmail.com>

License: [GPLv3+](LICENSE)

Language: [Python](https://python.org) 3

### Features

#### Target hardware

- [x] DN-500AV
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
    - [x] Presets! (-18dBFS, -24dBFS…)
    - [ ] SPL calibrated display (-18dBFS = 85dBSPL)
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

##### Windows executable

- [ ] Find a way to make it resident in the task bar with a nice icon, like soundcard control panel
    - [x] [RBTray](https://sourceforge.net/projects/rbtray/files/latest/download)
    - [x] [MinimizeToTray](https://github.com/sandwichdoge/MinimizeToTray/releases/latest)
    - [ ] The Pythonic Way
- [ ] Handle shutdown to power off the device
- [ ] PyInstaller
- [ ] VST plugin? (Not required if MIDI input is implemented but would be neat to have in the monitoring section of a
  DAW)
    - [ ] See [PyVST](https://pypi.org/project/pyvst/)

#### Mobile

- [ ] Autonomous mobile app? Kivy enables that!
    - [ ] Android
    - [ ] iOS/iPadOS