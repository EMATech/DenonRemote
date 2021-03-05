# -*- coding: utf-8 -*-
"""
Denon DN-500AV serial and IP communication protocol description
"""

import logging

logger = logging.getLogger(__name__)

commands = {
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
    'RM': "Remote Maintenance",
    'SS': "System Settings"
}

# FIXME: compute dynamically
commands_max_size = 4
commands_min_size = 2

# Page 93 (99 in PDF form)

pw_params = {
    'ON': "On",  # FIXME: Only available with IP control
    'STANDBY': "Standby"
}

# Undocumented
mv_subcommands = {
    'MAX': 'Maximum'
}

# FIXME: compute dynamically
mv_subcommands_max_size = 3
mv_subcommands_min_size = 3

mv_params = {
    'UP': "Up",
    'DOWN': "Down",
    # Computed
}


def srange(start, stop, step, length):
    """Generate consecutive numbers as fixed length strings"""
    i = float(start)
    while i < stop:
        result = str(int(i)).zfill(length)
        # Special volume case requires 3 characters for half dBs
        if i - int(i):
            result += '5'  # FIXME: hardcoded for now
        yield result
        i += step


MASTER_VOLUME_MIN = 0
MASTER_VOLUME_MAX = 100
MASTER_VOLUME_STEP = 0.5
MASTER_VOLUME_LEN = 2
MASTER_VOLUME_ZERODB_REF = 80


def compute_master_volume_label(value, zerodb_ref=MASTER_VOLUME_ZERODB_REF):
    """Convert Master Volume ASCII value to dB"""
    # TODO: Handle absolute values
    label = '---.-dB'
    if int(value[:2]) < MASTER_VOLUME_MIN or int(value[:2]) > MASTER_VOLUME_MAX:
        logger.error("Master volume value %s out of bounds (%s-%s)", value, MASTER_VOLUME_MIN, MASTER_VOLUME_MAX)
    # Quirks
    if value == '99':
        result = "-∞dB"
    elif value == '995':
        result = "-80.5dB"
    elif len(value) == 2:
        # General case
        result = str(float(value) - zerodb_ref)
    elif len(value) == 3:
        # Handle undocumented special case for half dB

        # Hardcode values around 0 because of computing sign uncertainty
        # FIXME: test '985' which seems invalid
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
        raise ValueError

    # Format label with fixed width like the actual display:
    # [ NEG SIGN or EMPTY ] [ DIGIT er EMPTY ] [ DIGIT ] [ DOT ] [ DIGIT ] [ d ] [ B ]
    label = "%s%s%s.%sdB" % (
        result[0] if result[0] == '-' else " ",
        " " if len(result) <= 3 or result[-4] == '-' else result[-4],
        result[-3],
        result[-1])

    logger.debug(label)
    return label


for volume_value in srange(MASTER_VOLUME_MIN, MASTER_VOLUME_MAX, MASTER_VOLUME_STEP, MASTER_VOLUME_LEN):
    mv_params[volume_value] = compute_master_volume_label(volume_value)

cv_subcommands = {
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

# FIXME: compute dynamically
cv_subcommands_max_size = 3
cv_subcommands_min_size = 1

cv_params = {
    'UP': "Up",
    'DOWN': "Down"
    # Computed
}

CHANNEL_VOLUME_MIN = 38
CHANNEL_VOLUME_MAX = 62
CHANNEL_VOLUME_STEP = 0.5
CHANNEL_VOLUME_LEN = 2
CHANNEL_VOLUME_ZERODB_REF = 50


def compute_channel_volume_label(value):
    """Convert Channel Volume ASCII value to dB"""
    label = ''
    # OOB check
    if int(value[:2]) < CHANNEL_VOLUME_MIN or int(value[:2]) > CHANNEL_VOLUME_MAX:
        logger.error("Channel volume value %s out of bounds (%s-%s)", value, CHANNEL_VOLUME_MIN,
                     CHANNEL_VOLUME_MAX)
    # General case
    if len(value) == 2:
        label = str(float(value) - CHANNEL_VOLUME_ZERODB_REF) + "dB"
    if len(value) == 3:
        # Handle undocumented special case for half dB
        label = str(int(value[:2]) - CHANNEL_VOLUME_ZERODB_REF) + ".5" + "dB"
    # Prepend positive values with +
    if int(value) - CHANNEL_VOLUME_ZERODB_REF >= 0:
        label = "+" + label
    return label


for volume_value in srange(CHANNEL_VOLUME_MIN, CHANNEL_VOLUME_MAX, CHANNEL_VOLUME_STEP, CHANNEL_VOLUME_LEN):
    cv_params[volume_value] = compute_channel_volume_label(volume_value)

mu_params = {
    'ON': "On",
    'OFF': "Off"
}

# Page 94 (100 in PDF form)

si_params = {
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

zm_params = mu_params

sd_params = {
    'AUTO': "Set AUTO mode",
    'HDMI': "Set force HDMI INPUT mode",
    'DIGITAL': "Set force DIGITAL INPUT (Optical, Coaxial) mode",
    'ANALOG': "Set force ANALOG INPUT mode"
}

dc_params = {
    'AUTO': "Set DIGITAL INPUT AUTO mode",
    'PCM': "Set DIGITAL INPUT force PCM mode",
    'DTS': "Set DIGITAL INPUT force DTS mode"
}

sv_params = {
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

slp_params = {
    'OFF': "Off",
    # TODO: generate integers conversion to min from 001 to 120 ASCII
    '010': "10 minutes"
}

# Page 95 (101 in PDF form)

ms_params = {
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

vs_params = {
    'AUDIO AMP': "Set HDMI AUDIO Output to AMP",
    'AUDIO TV': "Set HDMI AUDIO Output to TV",
    'VPMAUTO': "Set Video Processing Mode to AUTO",
    'VPMGAME': "Set Video Processing Mode to GAME",
    'VPMMOVIE': "Set Video Processing Mode to MOVIE",
}

# Pages 96-97 (102-103 in PDF form)
ps_subcommands = {
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

# FIXME: compute dynamically
ps_subcommands_max_size = 10
ps_subcommands_min_size = 2

# Page 96 (102 in PDF form)

ps_tone_params = mu_params
ps_sb_params = {
    'MTRX ON': "Matrix",
    'PLIIX CINEMA': "Dolby Pro Logic IIx Cinema",
    'PLIIX MUSIC': "Dolby Pro Logic IIx Music",
    'ON': "On",
    'OFF': "Off"
}
ps_eq_params = mu_params
ps_mode_params = {
    'MUSIC': "Music",
    'CINEMA': "Cinema",
    'GAME': "Game",
    'PRO LOGIC': "Dolby Pro Logic"
}
ps_fh_params = mu_params
ps_phg_params = {
    'LOW': "Low",
    'MID': "Mid",
    'HI': "High"
}
ps_bas_params = {
    # Computed
}

TONE_MIN = 44
TONE_MAX = 56
TONE_STEP = 1
TONE_LEN = 2
TONE_ZERODB_REF = 50


def compute_tone_volume_label(value):
    """Convert Tone ASCII value to dB"""
    # OOB Check
    label = ''
    if int(value) < TONE_MIN or int(value) > TONE_MAX:
        logger.error("Tone value %s out of bounds (%s-%s)", value, TONE_MIN, TONE_MAX)
    label = str(float(value) - TONE_ZERODB_REF) + "dB"
    # Prepend positive values with +
    if int(value) - TONE_ZERODB_REF >= 0:
        label = "+" + label
    return label


for volume_value in srange(TONE_MIN, TONE_MAX, TONE_STEP, TONE_LEN):
    ps_bas_params[volume_value] = compute_tone_volume_label(volume_value)

ps_tre_params = ps_bas_params
ps_drc_params = {
    'AUTO': "Auto",
    'LOW': "Low",
    'MID': "Mid",
    'HI': "High",
    'OFF': "Off"
}
ps_dco_params = {
    'OFF': "Off",
    'LOW': "Low",
    'MID': "Mid",
    'HI': "High"
}
ps_lfe_params = {
    # Computed
}

LFE_MIN = 0
LFE_MAX = 10
LFE_STEP = 1
LFE_LEN = 2
LFE_ZERODB_REF = 0


def compute_lfe_volume_label(value):
    """Convert lfe ASCII value to dB"""
    # OOB Check
    if int(value) < LFE_MIN or int(value) > LFE_MAX:
        logger.error("LFE value %s out of bounds (%s-%s)", value, LFE_MIN, LFE_MAX)
    label = str(float(value) - LFE_ZERODB_REF) + "dB"
    # All values are negative. Prepend positive values with -
    if int(value) == 0:
        label = "+" + label
    else:
        label = "-" + label
    return label


for volume_value in srange(LFE_MIN, LFE_MAX, LFE_STEP, LFE_LEN):
    ps_lfe_params[volume_value] = compute_lfe_volume_label(volume_value)

ps_eff_params = {
    # Computed
}

# Page 97 (103 in PDF form)

ps_del_params = {
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
ps_afd_params = mu_params
ps_pan_params = mu_params
ps_dim_params = {
    'UP': "Up",
    'DOWN': "Down",
    # TODO: generate integer conversion to dB (00 to 99 ASCII)
    '00': "0dB",
    '06': "6dB",
    # Stops at 6
}
ps_cen_params = {
    'UP': "Up",
    'DOWN': "Down",
    # TODO: generate integer conversion to dB (00 to 99 ASCII)
    '00': "0dB",
    '07': "7dB",
    # Stops at 7
}
ps_cei_params = {
    'UP': "Up",
    'DOWN': "Down",
    # TODO: generate integer conversion to dB (00 to 99 ASCII)
    '00': "0.0dB",
    '99': "1.0dB",
}
ps_sw_params = mu_params
ps_rsz_params = {
    'S': "Small",
    'MS': "Medium Small",
    'M': "Medium",
    'ML': "Medium Large",
    'L': "Large"
}
ps_delay_params = {
    'UP': "Up",
    'DOWN': "Down",
    # TODO: generate integer conversion to ms (000 to 999 ASCII)
    '000': "0ms",
    '200': "200ms",
    # Stops at 200ms
}
ps_rstr_params = {
    'OFF': "Off",
    'MODE1': "Mode 1",
    'MODE2': "Mode 2",
    'MODE3': "Mode 3"
}

ps_params = {
    'TONE CTRL': ps_tone_params,
    'SB:': ps_sb_params,
    'CINEMA EQ.': ps_eq_params,
    'MODE:': ps_mode_params,
    'FH': ps_fh_params,
    'PHG': ps_phg_params,
    'BAS': ps_bas_params,
    'TRE': ps_tre_params,
    'DRC': ps_drc_params,
    'DCO': ps_dco_params,
    'LFE': ps_lfe_params,
    'EFF': ps_eff_params,
    'DEL': ps_del_params,
    'AFD': ps_afd_params,
    'PAN': ps_pan_params,
    'DIM': ps_dim_params,
    'CEN': ps_cen_params,
    'CEI': ps_cei_params,
    'SWR': ps_sw_params,
    'RSZ': ps_rsz_params,
    'DELAY': ps_delay_params,
    'RSTR': ps_rstr_params
}
# Page 98 (104 in PDF form)

z2_params = {
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

z2mu_params = mu_params

z2cv_params = cv_params

z2slp_params = slp_params

# Page 99 (105 in PDF form)

ns_params = {
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

# Page 100 (106 in PDF form)

ip_params = {
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

# Page 101 (107 in PDF form)

mn_params = {
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

sy_params = {
    'REMOTE LOCK ON': "Remote Lock On",
    'REMOTE LOCK OFF': "Remote Lock Off",
    'PANEL LOCK ON': "Panel Button (Except Master Volume) Control Lock On",
    'PANEL+V LOCK ON': "Panel Button & Master Volume Control Lock On",
    'PANEL LOCK OFF': "Panel Button & Master Volume Control Lock Off"
}

ug_params = {
    # TODO: Handle response?
    'IDN': "ID Number for Upgrade"
}

rm_params = {
    'STA': "Remote Maintenance Mode Start",
    'END': "Remote Maintenance Mode Stop"
}

ss_params = {
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

commands_subcommands = {
    'MV': mv_subcommands,
    'CV': cv_subcommands,
    'PS': ps_subcommands
}

commands_subcommands_max_size = {
    'MV': mv_subcommands_max_size,
    'CV': cv_subcommands_max_size,
    'PS': ps_subcommands_max_size
}

commands_subcommands_min_size = {
    'MV': mv_subcommands_min_size,
    'CV': cv_subcommands_min_size,
    'PS': ps_subcommands_min_size
}

commands_params = {
    'PW': pw_params,
    'MV': mv_params,
    'CV': cv_params,
    'MU': mu_params,
    'SI': si_params,
    'ZM': zm_params,
    'SD': sd_params,
    'DC': dc_params,
    'SV': sv_params,
    'SLP': slp_params,
    'MS': ms_params,
    'VS': vs_params,
    'PS': ps_params,
    'Z2': z2_params,
    'Z2MU': z2mu_params,
    'Z2CV': z2cv_params,
    'Z2SLP': z2slp_params,
    'NS': ns_params,
    'IP': ip_params,
    'MN': mn_params,
    'SY': sy_params,
    'RM': rm_params,
    'SS': ss_params
}

# Page 102-109 (108-115 in PDF form)

status_requests = {
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

    command_code = None
    command_label = None
    subcommand_code = None
    subcommand_label = None
    parameter_code = None
    parameter_label = None
    response = None

    def __init__(self):
        pass

    def parse_response(self, status_command):
        # Handle strings and bytes
        if type(status_command) is bytes:
            # FIXME: some parts can be UTF-8 encoded
            status_command = status_command.decode('ASCII')
        logger.debug("Received status command: %s", status_command)

        # Commands are of known sizes. Try the largest first.
        for i in range(commands_max_size, commands_min_size - 1, -1):
            self.command_code = status_command[:i]
            self.command_label = commands.get(self.command_code)
            if self.command_label is not None:
                break

        if self.command_label is None:
            logger.error("Command unknown: %s", status_command)
            return
        else:
            logger.info("Parsed command %s: %s", self.command_code, self.command_label)

        # Trim command from status command stream
        status_command = status_command[len(self.command_code):]

        # Handle subcommands
        if commands_subcommands.get(self.command_code) is None:
            logger.debug("The command %s doesn't have any known subcommands.", self.command_code)
        else:
            logger.debug("Searching for subcommands in: %s", status_command)

            # Subcommands are of known sizes. Try the largest first.
            for i in range(commands_subcommands_max_size[self.command_code],
                           commands_subcommands_min_size[self.command_code] - 1, -1):
                self.subcommand_code = status_command[:i]
                self.subcommand_label = commands_subcommands[self.command_code].get(self.subcommand_code)
                if self.subcommand_label is not None:
                    break

            if self.subcommand_label is None:
                logger.debug("Subcommand unknown. Probably a parameter: %s", status_command)
                self.subcommand_code = None
            else:
                logger.info("Parsed subcommand %s: %s", self.subcommand_code, self.subcommand_label)
                # Trim subcommand from status command stream
                status_command = status_command[
                                 len(self.subcommand_code) + 1:]  # Subcommands have a space before the parameter

        # Handle parameters
        logger.debug("Searching for parameters in: %s", status_command)
        self.parameter_code = status_command
        if self.command_code == 'PS':
            self.parameter_label = commands_params[self.command_code][self.subcommand_code].get(self.parameter_code)
        else:
            self.parameter_label = commands_params[self.command_code].get(self.parameter_code)
        if self.parameter_label is None:
            logger.error("Parameter unknown: %s", status_command)
            self.parameter_code = None
        else:
            # Trim parameters from status command stream
            status_command = status_command[len(status_command):]

        # Handle unexpected leftovers
        if status_command:
            logger.error("Unexpected unparsed data found: %s", status_command)

        if self.subcommand_label:
            self.response = "%s, %s: %s" % (self.command_label, self.subcommand_label, self.parameter_label)
        else:
            self.response = "%s: %s" % (self.command_label, self.parameter_label)


class DN500AVFormat:
    mv_reverse_params = {}

    def __init__(self):
        self.mv_reverse_params = dict([(value, key) for key, value in mv_params.items()])

    def get_raw_volume_value_from_db_value(self, value):
        logger.debug('value: %s', value)
        raw_value = self.mv_reverse_params['value']
        logger.debug('rawvalue: %s', raw_value)
        return raw_value
