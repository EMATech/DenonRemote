# This Python file uses the following encoding: utf-8
#
# SPDX-FileCopyrightText: 2021-2022 Raphaël Doursenaud <rdoursenaud@free.fr>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Denon DN-500AV serial and IP communication protocol description

Derived from the manual (DN500AVEM_ENG-CD-ROM_v00.pdf)
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def srange(start: int | float, stop: int | float, step: int | float, length: int) -> str:
    """Generate consecutive numbers as fixed length strings"""
    i = float(start)
    while i < stop:
        result = str(int(i)).zfill(length)
        # Special volume case requires 3 characters for half dBs
        if i - int(i):
            result += '5'  # FIXME: hardcoded for now
        yield result
        i += step


# ----------


###
# COMMANDS
#
# Page 93-101 (99-107 in PDF form)
###
COMMANDS = {
    'PW': "Power",
    'MV': "Master Volume",
    'CV': "Channel Volume",
    'MU': "Output Mute",
    'SI': "Select Input Source",
    'ZM': "Main Zone",
    'SD': "Digital Source Status",
    'DC': "Digital Input Mode",
    'SV': "Video Select Mode",
    'SLP': "Main Zone Sleep Timer",
    'MS': "Select Surround Mode",
    'VS': "Select Video Mode",
    'PS': "Parameter Setting",
    'Z2': "Zone 2 Control",
    'Z2MU': "Zone 2 Mute",
    'Z2CV': "Zone 2 Channel Volume",
    'Z2SLP': "Zone 2 Sleep Timer",
    'NS': "NET/USB Control",
    'IP': "DOCK Control",
    'MN': "Menu Control",
    'SY': "System Control",
    'UG': "Upgrade",
    'RM': "Remote Maintenance",
    'SS': "System Settings"
}

# FIXME: compute dynamically
COMMANDS_MAX_SIZE = 4
COMMANDS_MIN_SIZE = 2

# ----------
# Page 93 (99 in PDF form)


###
# POWER
##
PW_PARAMS = {
    'ON': "On",  # FIXME: Only available with IP control. Delay next command by one second.
    'STANDBY': "Standby"
}

###
# MASTER VOLUME
###
MASTER_VOLUME_MIN = 0
MASTER_VOLUME_MAX = 99
MASTER_VOLUME_STEP = 0.5
MASTER_VOLUME_ZERODB_REF = 80
VOLUME_MIN_LEN = 2
VOLUME_MAX_LEN = 3

MV_SUBCOMMANDS = {  # Undocumented
    'MAX': 'Maximum'
}

# FIXME: compute dynamically
MV_SUBCOMMANDS_MAX_SIZE = 3
MV_SUBCOMMANDS_MIN_SIZE = 3

MV_PARAMS = {
    'UP': "Up",
    'DOWN': "Down",
    # + Computed volume values
}


def compute_master_volume_label(value: str, zerodb_ref: int = MASTER_VOLUME_ZERODB_REF) -> str:
    """Convert Master Volume ASCII value to dB"""
    # TODO: Handle absolute values
    label = '---.-dB'
    result = None
    if int(value[:2]) < MASTER_VOLUME_MIN or int(value[:2]) > MASTER_VOLUME_MAX:
        logger.error(f"Master volume value {value} out of bounds ({MASTER_VOLUME_MIN}-{MASTER_VOLUME_MAX})")
    # Quirks
    elif len(value) == VOLUME_MIN_LEN:
        if value == '99':
            result = ""  # Minus inf
        else:
            # General case
            result = str(float(value) - zerodb_ref)
    elif len(value) == VOLUME_MAX_LEN:
        # Handle undocumented special case for half dB

        if value == '995':
            result = "-80.5"
        else:

            # Hardcode values around 0 because of computing sign uncertainty
            if value == str((zerodb_ref - 1)) + '5':
                result = "-0.5"
            elif value == str(zerodb_ref) + '5':
                result = "0.5"
            else:
                value = int(value[:2])  # Drop the third digit
                offset = 0
                if value < zerodb_ref:
                    offset = 1
                logger.debug("Add offset %i to dB calculation with value %i5", offset, value)
                result = str(int(value + offset - zerodb_ref)) + ".5"
    else:
        logger.error(f"Master volume value {value} of lenghth {len(value)} is unparsable")
        raise ValueError

    # Format label with fixed width like the actual display:
    # [ NEG SIGN or EMPTY ] [ DIGIT er EMPTY ] [ DIGIT ] [ DOT ] [ DIGIT ] [ d ] [ B ]
    if result:
        label = "%s%s%s.%sdB" % (
            result[0] if result[0] == '-' else " ",
            " " if len(result) <= 3 or result[-4] == '-' else result[-4],
            result[-3],
            result[-1])

    logger.debug(label)
    return label


for volume_value in srange(MASTER_VOLUME_MIN, MASTER_VOLUME_MAX, MASTER_VOLUME_STEP, VOLUME_MIN_LEN):
    MV_PARAMS[volume_value] = compute_master_volume_label(volume_value)

###
# CHANNEL VOLUME
###
CHANNEL_VOLUME_MIN = 38
CHANNEL_VOLUME_MAX = 62
CHANNEL_VOLUME_STEP = 0.5
SW_OFF = 0
CHANNEL_VOLUME_ZERODB_REF = 50

# FIXME: compute dynamically
CV_SUBCOMMANDS_MAX_SIZE = 3
CV_SUBCOMMANDS_MIN_SIZE = 1

CV_SUBCOMMANDS = {
    'FL': "Front Left",
    'FR': "Front Right",
    'C': "Center",
    'SW': "Subwoofer",
    'SL': "Surround Left",
    'SR': "Surround Right",
    # SBch 2SP
    'SBL': "Surround Back Left",
    'SBR': "Surround Back Right",
    # SBch 1SP
    'SB': "Surround Back",
    'FHL': "Front Height Left",
    'FHR': "Front Height Right"
}

CV_PARAMS = {
    'UP': "Up",
    'DOWN': "Down"
    # + Computed volume values
}


def compute_channel_volume_label(value: str) -> str:
    """Convert Channel Volume ASCII value to dB"""
    label = ''
    # OOB check
    if int(value[:2]) < CHANNEL_VOLUME_MIN or int(value[:2]) > CHANNEL_VOLUME_MAX:
        logger.error(f"Channel volume value {value} out of bounds ({CHANNEL_VOLUME_MIN}-{CHANNEL_VOLUME_MAX})")
    # General case
    if len(value) == VOLUME_MIN_LEN:
        label = str(float(value) - CHANNEL_VOLUME_ZERODB_REF) + "dB"
    if len(value) == VOLUME_MAX_LEN:
        # Handle undocumented special case for half dB
        label = str(int(value[:2]) - CHANNEL_VOLUME_ZERODB_REF) + ".5" + "dB"
    # Prepend positive values with +
    if int(value) - CHANNEL_VOLUME_ZERODB_REF >= 0:
        label = "+" + label
    return label


for volume_value in srange(CHANNEL_VOLUME_MIN, CHANNEL_VOLUME_MAX, CHANNEL_VOLUME_STEP, VOLUME_MIN_LEN):
    CV_PARAMS[volume_value] = compute_channel_volume_label(volume_value)

###
# MUTE
###
MU_PARAMS = {
    'ON': "On",
    'OFF': "Off"
}

# ----------
# Page 94 (100 in PDF form)


###
# SELECT INPUT
###
SI_PARAMS = {
    'CD': "CD",
    'DVD': "DVD",
    'BD': "BD",
    'TV': "TV",
    'SAT/CBL': "SAT/CBL",
    'GAME': "GAME",
    'GAME2': "GAME 2",
    'DOCK': "DOCK",
    'V.AUX': "VIDEO AUX",
    'IPOD': "IPOD",
    'NET/USB': "NET/USB",
    'SERVER': "SERVER",
    'FAVORITES': "FAVORITES",
    'USB/IPOD': "USB/IPOD",
    'USB': "USB",
    'IPD': "IPD"
}

###
# ZONE MAIN
###
ZM_PARAMS = MU_PARAMS

###
# INPUT MODE
###
SD_PARAMS = {
    'AUTO': "Set AUTO mode",
    'HDMI': "Set force HDMI INPUT mode",
    'DIGITAL': "Set force DIGITAL INPUT (Optical, Coaxial) mode",
    'ANALOG': "Set force ANALOG INPUT mode"
}

###
# DECODE MODE
###
DC_PARAMS = {
    'AUTO': "Set DIGITAL INPUT AUTO mode",
    'PCM': "Set DIGITAL INPUT force PCM mode",
    'DTS': "Set DIGITAL INPUT force DTS mode"
}

###
# VIDEO SOURCE
###
SV_PARAMS = {
    'DVD': "DVD",
    'BD': "BD",
    'TV': "TV",
    'SAT/CBL': "SAT/CBL",
    'GAME': "GAME",
    'GAME2': "GAME 2",
    'DOCK': "DOCK",
    'V.AUX': "VIDEO AUX",
    'SOURCE': "Cancel (Source)"
}

###
# SLEEP TIMER
###
SLP_PARAMS = {
    'OFF': "Off",
    # TODO: generate integers conversion to min from 001 to 120 ASCII
    '010': "10 minutes"
}

# ----------
# Page 95 (101 in PDF form)


###
# SURROUND MODE
##
MS_PARAMS = {
    # Surround
    'MOVIE': "Movie",
    'MUSIC': "Music",
    'GAME': "Game",
    'DIRECT': "Direct",
    'PURE DIRECT': "Pure Direct",
    'STEREO': "Stereo",
    'STANDARD': "Standard",
    'DOLBY DIGITAL': "Dolby Digital",
    'DTS SURROUND': "DTS Surround",
    'MCH STEREO': "Multi-channel Stereo",
    'ROCK ARENA': "Rock Arena",
    'JAZZ CLUB': "Jazz Club",
    'CLASSIC CONCERT': "Classic Concert",
    'MONO MOVIE': "Mono Movie",
    'MATRIX': "Matrix",
    'VIDEO GAME': "Video Game",
    'VIRTUAL': "Virtual Surround",
    # Quick Select Mode
    'QUICK1': "Quick Select 1 Mode",
    'QUICK2': "Quick Select 2 Mode",
    'QUICK3': "Quick Select 3 Mode",
    'QUICK4': "Quick Select 4 Mode",
    # Quick Select Mode Memory
    'QUICK1 MEMORY': "Quick Select 1 Mode Memory",
    'QUICK2 MEMORY': "Quick Select 2 Mode Memory",
    'QUICK3 MEMORY': "Quick Select 3 Mode Memory",
    'QUICK4 MEMORY': "Quick Select 4 Mode Memory",
    # Undocumented
    'MULTI CH IN': "Multiple Channels Input",
    'DTS HD MSTR': "DTS HD Master",
    'DTS96/24': "DTS 96/24"
}

###
# VIDEO SELECT
###
VS_PARAMS = {  # TODO: separate AUDIO subcommand?
    'AUDIO AMP': "Set HDMI AUDIO Output to AMP",
    'AUDIO TV': "Set HDMI AUDIO Output to TV",
    'VPMAUTO': "Set Video Processing Mode to AUTO",
    'VPMGAME': "Set Video Processing Mode to GAME",
    'VPMMOVIE': "Set Video Processing Mode to MOVIE",
}

# ----------

###
# PARAMETER SETTING
# Pages 96-97 (102-103 in PDF form)
###
# FIXME: compute dynamically
PS_SUBCOMMANDS_MAX_SIZE = 10
PS_SUBCOMMANDS_MIN_SIZE = 2

PS_SUBCOMMANDS = {
    'TONE CTRL': "Tone Control",
    'SB:': "Surround Back Speaker Mode",
    'CINEMA EQ.': "Cinema EQ",
    'MODE:': "Mode",
    'FH': "Front Height (Dolby Pro Logic IIz Height) Output",
    'PHG': "Dolby Pro Logic IIz Height Gain",
    'BAS': "Bass",
    'TRE': "Treble",
    'DRC': "DRC",
    'DCO': "D.COMP",
    'LFE': "Low Frequency Effects",
    'EFF': "Effect Level",
    'DEL': "Delay",
    'AFD': "Auto Flag Detect Mode",
    'PAN': "Panorama",
    'DIM': "Dimension",
    'CEN': "Center Width",
    'CEI': "Center Image",
    'SWR': "Subwoofer",
    'RSZ': "Room Size",
    'DELAY': "Audio Delay",
    'RSTR': "Audio Restorer"
}

# ----------
# Page 96 (102 in PDF form)


###
# TONE CONTROL
###
TONE_MIN = 44
TONE_MAX = 56
TONE_STEP = 1
TONE_LEN = 2
TONE_ZERODB_REF = 50

PS_TONE_PARAMS = MU_PARAMS
PS_SB_PARAMS = {
    'MTRX ON': "Matrix",
    'PLIIX CINEMA': "Dolby Pro Logic IIx Cinema",
    'PLIIX MUSIC': "Dolby Pro Logic IIx Music",
    'ON': "On",
    'OFF': "Off"
}
PS_EQ_PARAMS = MU_PARAMS
PS_MODE_PARAMS = {
    'MUSIC': "Music",
    'CINEMA': "Cinema",
    'GAME': "Game",
    'PRO LOGIC': "Dolby Pro Logic"
}
PS_FH_PARAMS = MU_PARAMS
PS_PHG_PARAMS = {
    'LOW': "Low",
    'MID': "Mid",
    'HI': "High"
}
PS_BAS_PARAMS = {
    # Computed
}


def compute_tone_volume_label(value: str) -> str:
    """Convert Tone ASCII value to dB"""
    # OOB Check
    label = ''
    if int(value) < TONE_MIN or int(value) > TONE_MAX:
        logger.error(f"Tone value {value} out of bounds ({TONE_MIN}-{TONE_MAX})")
    label = str(float(value) - TONE_ZERODB_REF) + "dB"
    # Prepend positive values with +
    if int(value) - TONE_ZERODB_REF >= 0:
        label = "+" + label
    return label


for volume_value in srange(TONE_MIN, TONE_MAX, TONE_STEP, TONE_LEN):
    PS_BAS_PARAMS[volume_value] = compute_tone_volume_label(volume_value)

PS_TRE_PARAMS = PS_BAS_PARAMS
PS_DRC_PARAMS = {
    'AUTO': "Auto",
    'LOW': "Low",
    'MID': "Mid",
    'HI': "High",
    'OFF': "Off"
}
PS_DCO_PARAMS = {
    'OFF': "Off",
    'LOW': "Low",
    'MID': "Mid",
    'HI': "High"
}

###
# LFE LEVEL
###
LFE_MIN = 0  # Maximum
LFE_MAX = 10  # Minus
LFE_STEP = 1
LFE_LEN = 2
LFE_ZERODB_REF = 0

PS_LFE_PARAMS = {
    'UP': "Up",
    'DOWN': "Down",
    # + Computed volume values
}


def compute_lfe_volume_label(value: str) -> str:
    """Convert LFE ASCII value to dB"""
    if int(value) < LFE_MIN or int(value) > LFE_MAX:
        logger.error(f"LFE value {value} out of bounds ({LFE_MIN}-{LFE_MAX})")
    label = str(float(value) - LFE_ZERODB_REF) + "dB"
    # All values are negative. Prepend positive values with -.
    if int(value) == 0:
        label = "+" + label
    else:
        label = "-" + label
    return label


for volume_value in srange(LFE_MIN, LFE_MAX, LFE_STEP, LFE_LEN):
    PS_LFE_PARAMS[volume_value] = compute_lfe_volume_label(volume_value)

###
# EFFECT LEVEL
###
EFF_MIN = 1
EFF_MAX = 15
EFF_DEFAULT = 10
EFF_STEP = 1
EFF_LEN = 2
EFF_ZERODB_REF = 0

PS_EFF_PARAMS = {
    'UP': "Up",
    'DOWN': "Down",
    # + Computed volume values
}


def compute_eff_volume_label(value: str) -> str:
    """Convert EFF ASCII value to dB"""
    if int(value) < EFF_MIN or int(value) > EFF_MAX:
        logger.error(f"EFF value {value} out of bounds ({EFF_MIN}-{EFF_MAX})")
    label = str(float(value) - EFF_ZERODB_REF) + "dB"
    # All values are positive. Prepend values with +.
    return "+" + label


for volume_value in srange(EFF_MIN, EFF_MAX, EFF_STEP, EFF_LEN):
    PS_EFF_PARAMS[volume_value] = compute_eff_volume_label(volume_value)

# ----------
# Page 97 (103 in PDF form)

###
# EFFECTS DELAY TIME
###
PS_DEL_PARAMS = {
    'UP': "Up",
    'DOWN': "Down",
    # TODO: generate integer conversion to ms (000 to 999 ASCII)
    # 3ms/step
    '000': "0ms",
    '060': "60ms",
    # 10ms/step
    '070': "70ms",
    '300': "300ms"
    # Stops at 300ms
}

PS_AFD_PARAMS = MU_PARAMS
PS_PAN_PARAMS = MU_PARAMS
PS_DIM_PARAMS = {
    'UP': "Up",
    'DOWN': "Down",
    # TODO: generate integer conversion to dB (00 to 99 ASCII)
    '00': "0dB",
    '06': "6dB",
    # Stops at 6
}
PS_CEN_PARAMS = {
    'UP': "Up",
    'DOWN': "Down",
    # TODO: generate integer conversion to dB (00 to 99 ASCII)
    '00': "0dB",
    '07': "7dB",
    # Stops at 7
}
PS_CEI_PARAMS = {
    'UP': "Up",
    'DOWN': "Down",
    # TODO: generate integer conversion to dB (00 to 99 ASCII)
    '00': "0.0dB",
    '99': "1.0dB",
}
PS_SW_PARAMS = MU_PARAMS
PS_RSZ_PARAMS = {
    'S': "Small",
    'MS': "Medium Small",
    'M': "Medium",
    'ML': "Medium Large",
    'L': "Large"
}

###
# AUDIO DELAY
###
# FIXME: Report firmware bug: always returns 000.
PS_DELAY_PARAMS = {
    'UP': "Up",
    'DOWN': "Down",
    # TODO: generate integer conversion to ms (000 to 999 ASCII)
    '000': "0ms",
    '200': "200ms",
    # Stops at 200ms
}

###
# AUDIO RESTORER
###
PS_RSTR_PARAMS = {
    'OFF': "Off",
    'MODE1': "Mode 1",
    'MODE2': "Mode 2",
    'MODE3': "Mode 3"
}

PS_PARAMS = {
    'TONE CTRL': PS_TONE_PARAMS,
    'SB:': PS_SB_PARAMS,
    'CINEMA EQ.': PS_EQ_PARAMS,
    'MODE:': PS_MODE_PARAMS,
    'FH': PS_FH_PARAMS,
    'PHG': PS_PHG_PARAMS,
    'BAS': PS_BAS_PARAMS,
    'TRE': PS_TRE_PARAMS,
    'DRC': PS_DRC_PARAMS,
    'DCO': PS_DCO_PARAMS,
    'LFE': PS_LFE_PARAMS,
    'EFF': PS_EFF_PARAMS,
    'DEL': PS_DEL_PARAMS,
    'AFD': PS_AFD_PARAMS,
    'PAN': PS_PAN_PARAMS,
    'DIM': PS_DIM_PARAMS,
    'CEN': PS_CEN_PARAMS,
    'CEI': PS_CEI_PARAMS,
    'SWR': PS_SW_PARAMS,
    'RSZ': PS_RSZ_PARAMS,
    'DELAY': PS_DELAY_PARAMS,
    'RSTR': PS_RSTR_PARAMS
}

# ----------
# Page 98 (104 in PDF form)

###
# ZONE 2 parameters
###
# FIXME: untested!
# z2_params = si_params
Z2_PARAMS = {
    'CD': "CD",
    'DVD': "DVD",
    'BD': "BD",
    'SAT/CBL': "SAT/CBL",
    'DOCK': "DOCK",
    'V.AUX': "VIDEO AUX",
    'IPOD': "IPOD",
    'NET/USB': "NET/USB",
    'SERVER': "SERVER",
    'FAVORITES': "FAVORITES",
    'USB/IPOD': "USB/IPOD",
}

Z2MU_PARAMS = MU_PARAMS

Z2CV_PARAMS = CV_PARAMS

Z2SLP_PARAMS = SLP_PARAMS

# ----------
# Page 99 (105 in PDF form)


###
# NETWORK AUDIO / USB / IPOD
###
NS_PARAMS = {
    '90': "Cursor Up",
    '91': "Cursor Down",
    '92': "Cursor Left",
    '93': "Cursor Right",
    '94': "Enter (Play/Pause)",
    '9A': "Play",
    '9B': "Pause",
    '9C': "Stop",
    '9D': "Skip Plus",
    '9E': "Skip Minus",
    '9H': "Repeat One",  # Media Server, USB, iPod Direct
    '9I': "Repeat All",  # Media Server, USB, iPod Direct
    '9J': "Repeat Off",  # Media Server, USB, iPod Direct
    '9K': "Random On / Shuffle Songs",  # Media Server, USB / iPod Direct
    '9M': "Random Off / Shuffle Off",  # Media Server, USB / iPod Direct
    '9W': "Toggle Browse Mode/Remote Mode control",  # iPod Direct only
    '9X': "Page Next",
    '9Y': "Page Previous",
    # TODO: handle Return
    'H': "Net Audio Preset Name",  # UTF-8
    'FV MEM': "Add Favorites Folder",
    'P1 MEM': "Favorites 1 Memory",
    'P2 MEM': "Favorites 2 Memory",
    'P3 MEM': "Favorites 3 Memory"
}

# ----------
# Page 100 (106 in PDF form)


###
# IPOD CONTROL
###
IP_PARAMS = {
    '90': "Cursor Up",
    '91': "Cursor Down",
    '92': "Cursor Left",
    '93': "Cursor Right",
    '94': "Enter (Play/Pause)",
    '9A': "Play/Pause",
    '9C': "Stop",
    '9D': "Skip Plus",
    '9E': "Skip Minus",
    '9F': "Manual Search Plus",  # ASD-1R/11R/3/51
    '9G': "Manual Search Minus",  # ASD-1R/11R/3/51
    '9H': "Repeat One",  # ASD-1R/11R/3/51
    '9I': "Repeat All",  # ASD-1R/11R/3/51
    '9J': "Repeat Off",  # ASD-1R/11R/3/51
    '9K': "Shuffle Songs",  # ASD-1R/11R/3/51
    '9L': "Shuffle Album",  # ASD-1R/11R/3/51
    '9M': "Shuffle Off",  # ASD-1R/11R/3/51
    '9N': "Menu",  # ASD-1R/11R/3/51
    '9P': "Browse Mode",  # ASD-1R/11R/3/51
    '9Q': "Remote Mode",  # ASD-1R/11R/3/51
    '9X': "Page Next",
    '9Y': "Page Previous",
}

# ----------
# Page 101 (107 in PDF form)


###
# CURSOR CONTROL
###
MN_PARAMS = {
    'CUP': "Cursor Up",
    'CDN': "Cursor Down",
    'CLT': "Cursor Left",
    'CRT': "Cursor Right",
    'ENT': "Enter",
    'RTN': "Return",
    'MEN ON': "GUI Menu On",
    'MEN OFF': "GUI Menu Off",
    'SRC ON': "GUI Source Select Menu On",
    'SRC OFF': "GUI Source Select Menu Off"
}

###
# SYSTEM LOCK
###
SY_PARAMS = {
    'REMOTE LOCK ON': "Remote Lock On",
    'REMOTE LOCK OFF': "Remote Lock Off",
    'PANEL LOCK ON': "Panel Button (Except Master Volume) Control Lock On",
    'PANEL+V LOCK ON': "Panel Button & Master Volume Control Lock On",
    'PANEL LOCK OFF': "Panel Button & Master Volume Control Lock Off"
}

###
# UPGRADE ID
###
UG_PARAMS = {
    # TODO: Handle response?
    'IDN': "ID Number for Upgrade"
}

###
# REMOTE MAINTENANCE
###
RM_PARAMS = {
    'STA': "Remote Maintenance Mode Start",
    'END': "Remote Maintenance Mode Stop"
}

###
# SCREEN SAVER
###
SS_PARAMS = {
    'HOSALS ON': "Auto Lip Sync Disable",  # TODO: seems reversed. Check!
    'HOSALS OFF': "Auto Lip Sync Enable",  # TODO: seems reversed. Check!
    'OSDSCR ON': "Screen Saver Off",  # TODO: seems reversed. Check!
    'OSDSCR OFF': "Screen Saver On",  # TODO: seems reversed. Check!
    # Undocumented
    'VCTZMADIS ABS': "Volume Control Display Absolute",
    'VCTZMADIS REL': "Volume Control Display Relative",
    'VCTZMALIM OFF': "Volume Control limit Off",
    'VCTZMALIM 060': "Volume Control limit -20dB",
    'VCTZMALIM 070': "Volume Control limit -10dB",
    'VCTZMALIM 080': "Volume Control limit 0dB",
    'VCTZMAPON 50': "Volume Control Power On: -30dB"  # FIXME: value seems to follow mv_params convention
}

# ----------


###
# LOOKUP TABLES
###
COMMANDS_SUBCOMMANDS = {
    'MV': MV_SUBCOMMANDS,
    'CV': CV_SUBCOMMANDS,
    'PS': PS_SUBCOMMANDS
}

COMMANDS_SUBCOMMANDS_MAX_SIZE = {
    'MV': MV_SUBCOMMANDS_MAX_SIZE,
    'CV': CV_SUBCOMMANDS_MAX_SIZE,
    'PS': PS_SUBCOMMANDS_MAX_SIZE
}

COMMANDS_SUBCOMMANDS_MIN_SIZE = {
    'MV': MV_SUBCOMMANDS_MIN_SIZE,
    'CV': CV_SUBCOMMANDS_MIN_SIZE,
    'PS': PS_SUBCOMMANDS_MIN_SIZE
}

COMMANDS_PARAMS = {
    'PW': PW_PARAMS,
    'MV': MV_PARAMS,
    'CV': CV_PARAMS,
    'MU': MU_PARAMS,
    'SI': SI_PARAMS,
    'ZM': ZM_PARAMS,
    'SD': SD_PARAMS,
    'DC': DC_PARAMS,
    'SV': SV_PARAMS,
    'SLP': SLP_PARAMS,
    'MS': MS_PARAMS,
    'VS': VS_PARAMS,
    'PS': PS_PARAMS,
    'Z2': Z2_PARAMS,
    'Z2MU': Z2MU_PARAMS,
    'Z2CV': Z2CV_PARAMS,
    'Z2SLP': Z2SLP_PARAMS,
    'NS': NS_PARAMS,
    'IP': IP_PARAMS,
    'MN': MN_PARAMS,
    'SY': SY_PARAMS,
    'RM': RM_PARAMS,
    'SS': SS_PARAMS
}

# ----------
# Page 102-109 (108-115 in PDF form)


###
# STATUS REQUEST AND STATUS INFORMATION
###
STATUS_REQUESTS = {
    'PW?': "Power Status",
    'MV?': "Master Volume",
    'CV?': "Channel Volume",
    'MU?': "Output Mute",
    'SI?': "Selected Input Source",
    'ZM?': "Main Zone",
    'SD?': "Digital Source Status",
    'DC?': "Digital Input Mode",
    'SV?': "Video Select Mode",
    'SLP?': "Main Zone Sleep Timer",
    'MS?': "Surround Mode",
    'MSQUICK ?': "Quick Select Mode",
    'VSAUDIO ?': "Select Video Mode Audio",
    'VSVPN ?': "Video Processing Mode",  # TODO: Check if typo in manual or in firmware (Should be VSVPM)
    'PSTONE CTRL?': "Parameter Setting Tone Control",
    'PSSB: ?': "Parameter Setting Surround Back Speaker Mode",
    'PSCINEMA EQ. ?': "Parameter Setting Cinema EQ",
    'PSMODE: ?': "Parameter Setting Mode",
    'PSFH: ?': "Parameter Setting Mode Front Height (Dolby Pro Logic IIz) Output",
    'PSPHG ?': "Parameter Setting Dolby Pro Logic IIz Height Gain",
    'PSBAS ?': "Parameter Setting Bass",
    'PSTRE ?': "Parameter Setting Treble",
    'PSDRC ?': "Parameter Setting DRC",
    'PSDCO ?': "Parameter Setting D.Comp",
    'PSLFE ?': "Parameter Setting Low Frequency Effect",
    'PSEFF ?': "Parameter Setting Effect Level",
    'PSDEL ?': "Parameter Setting Delay",
    'PSAFD ?': "Parameter Setting Auto Flag Detect Mode",
    'PSPAN ?': "Parameter Setting Panorama",
    'PSDIM ?': "Parameter Setting Dimension",
    'PSCEN ?': "Parameter Setting Center Width",
    'PSCEI ?': "Parameter Setting Center Image",
    'PSSWR ?': "Parameter Setting Subwoofer",
    'PSRSZ ?': "Parameter Setting Room Size",
    'PSDELAY ?': "Parameter Setting Audio Delay",
    'PSRSTR ?': "Parameter Setting Audio Restorer",
    'Z2?': "Zone 2 Status",
    'Z2MU?': "Zone 2 Output Mute",
    'Z2QUICK ?': "Zone 2 Quick Select Memory",
    'Z2CV?': "Zone 2 Channel Volume",
    'Z2SLP?': "Zone 2 Sleep Timer",
    'NSA': "Onscreen Display Info List (ASCII mode)",
    'NSE': "Onscreen Display Info List (UTF-8 mode)",
    'RM?': "System Control Remote Status",
    'HOS ?': "System Control - HOS (HDMI Setup) Status",
    'OSD ?': "System Control - GUI Setting Status"
}


# TODO: abstract device


class DN500AVMessage:
    # From DN-500 manual (DN-500AVEM_ENG_CD-ROM_v00.pdf)
    # Pages 93-101 (99-107 in PDF form)

    command_code: None | str = None
    command_label: None | str = None
    subcommand_code: None | str = None
    subcommand_label: None | str = None
    parameter_code: None | str = None
    parameter_label: None | str = None
    response: None | str = None

    def __init__(self) -> None:
        pass

    def parse_response(self, status_command: str | bytes, unicode: bool = False) -> None:
        """
        Parses status command responses from a DN500AV into its components

        :param status_command: Status command response to parse
        :param unicode: Decode using UTF-8 rather than ASCII. Use after sending the NSE command.
        :return: Parsed string
        """
        # Handle strings and bytes
        if isinstance(status_command, bytes):
            if unicode:
                # Parts can be UTF-8 encoded when using the NSE command
                status_command = status_command.decode('UTF-8')
            else:
                status_command = status_command.decode('ASCII')

        logger.debug(f"Received status command: {status_command}")

        # Commands are of known sizes. Try the largest first.
        for i in range(COMMANDS_MAX_SIZE, COMMANDS_MIN_SIZE - 1, -1):
            self.command_code = status_command[:i]
            self.command_label = COMMANDS.get(self.command_code)
            if self.command_label is not None:
                break

        if self.command_label is None:
            logger.error(f"Command unknown: {status_command}")
            return

        logger.info(f"Parsed command {self.command_code}: {self.command_label}")

        # Trim command from status command stream
        status_command = status_command[len(self.command_code):]

        # Handle subcommands
        if COMMANDS_SUBCOMMANDS.get(self.command_code) is None:
            logger.debug(f"The command {self.command_code} doesn't have any known subcommands.")
        else:
            logger.debug(f"Searching for subcommands in: {status_command}")

            # Subcommands are of known sizes. Try the largest first.
            for i in range(COMMANDS_SUBCOMMANDS_MAX_SIZE[self.command_code],
                           COMMANDS_SUBCOMMANDS_MIN_SIZE[self.command_code] - 1, -1):
                self.subcommand_code = status_command[:i]
                self.subcommand_label = COMMANDS_SUBCOMMANDS[self.command_code].get(self.subcommand_code)
                if self.subcommand_label is not None:
                    break

            if self.subcommand_label is None:
                logger.debug(f"Subcommand unknown. Probably a parameter: {status_command}")
                self.subcommand_code = None
            else:
                logger.info(f"Parsed subcommand {self.subcommand_code}: {self.subcommand_label}")
                # Trim subcommand from status command stream
                status_command = status_command[
                                 len(self.subcommand_code) + 1:]  # Subcommands have a space before the parameter

        # Handle parameters
        logger.debug(f"Searching for parameters in: {status_command}")
        self.parameter_code = status_command
        if self.command_code == 'PS':
            self.parameter_label = COMMANDS_PARAMS[self.command_code][self.subcommand_code].get(self.parameter_code)
        else:
            self.parameter_label = COMMANDS_PARAMS[self.command_code].get(self.parameter_code)
        if self.parameter_label is None:
            logger.error(f"Parameter unknown: {status_command}")
            self.parameter_code = None
        else:
            # Trim parameters from status command stream
            status_command = status_command[len(status_command):]

        # Handle unexpected leftovers
        if status_command:
            logger.error(f"Unexpected unparsed data found: {status_command}")

        if self.subcommand_label:
            self.response = f"{self.command_label}, {self.subcommand_label}: {self.parameter_label}"
        else:
            self.response = f"{self.command_label}: {self.parameter_label}"


class DN500AVFormat:
    def __init__(self) -> None:
        self.mv_reverse_params: dict[str:str] = {value: key for key, value in MV_PARAMS.items()}

    def get_raw_volume_value_from_db_value(self, value: str) -> str:
        logger.debug(f"value: {value}")
        raw_value = self.mv_reverse_params['value']
        logger.debug(f"rawvalue: {raw_value}")
        return raw_value
