"""ITU-R M.493-16 symbol definitions.

All values from ITU-R M.493-16 (12/2023) Table A1-3.
Symbols 0-99 are decimal digit pairs (Table A1-2).
Symbols 100-127 are service commands.
"""

from enum import IntEnum

# Format specifiers (from Table A1-3)
SYM_DISTRESS = 112
SYM_ALL_SHIPS = 116
SYM_GROUP = 114
SYM_INDIVIDUAL = 120
SYM_GEO_AREA = 102
SYM_INDIVIDUAL_AUTO = 123
SYM_ACK = 112  # distress ack uses format 112

# Categories of call (from Table A1-3)
SYM_CAT_DISTRESS = 112
SYM_CAT_URGENCY = 110
SYM_CAT_SAFETY = 108
SYM_CAT_ROUTINE = 100

# Nature of distress (from Table A1-3)
SYM_NATURE_FIRE = 100
SYM_NATURE_FLOODING = 101
SYM_NATURE_COLLISION = 102
SYM_NATURE_GROUNDING = 103
SYM_NATURE_LISTING = 104
SYM_NATURE_SINKING = 105
SYM_NATURE_DISABLED = 106
SYM_NATURE_UNDESIGNATED = 107
SYM_NATURE_ABANDONING = 108
SYM_NATURE_PIRACY = 109
SYM_NATURE_MAN_OVERBOARD = 110

# First telecommands (from Table A1-3)
SYM_TC1_F3E_G3E_ALL = 100
SYM_TC1_F3E_G3E_DUPLEX = 101
SYM_TC1_POLLING = 103
SYM_TC1_UNABLE_COMPLY = 104
SYM_TC1_END_OF_CALL = 105
SYM_TC1_DATA = 106
SYM_TC1_J3E_TP = 109
SYM_TC1_DISTRESS_ACK = 110
SYM_TC1_DISTRESS_RELAY = 112
SYM_TC1_F1B_J2B_TTY_FEC = 113
SYM_TC1_F1B_J2B_TTY_ARQ = 115
SYM_TC1_TEST = 118
SYM_TC1_SHIP_POS_UPDATE = 121

# Second telecommands (from Table A1-3)
SYM_TC2_NO_REASON = 100
SYM_TC2_CONGESTION = 101
SYM_TC2_BUSY = 102
SYM_TC2_QUEUE = 103
SYM_TC2_STATION_BARRED = 104
SYM_TC2_NO_OPERATOR = 105
SYM_TC2_OP_TEMP_UNAVAIL = 106
SYM_TC2_EQUIP_DISABLED = 107
SYM_TC2_UNABLE_CHANNEL = 108
SYM_TC2_UNABLE_MODE = 109
SYM_TC2_SHIPS_AIRCRAFT = 110
SYM_TC2_MEDICAL = 111
SYM_TC2_PAY_PHONE = 112
SYM_TC2_FACSIMILE = 113
SYM_TC2_NO_INFO = 126

# End of sequence (from Table A1-3, Section 9)
SYM_EOS_ACK_RQ = 117
SYM_EOS_ACK_BQ = 122
SYM_EOS_EOT = 127

# Phasing symbols (from Table A1-3, Section 3)
SYM_PHASING_DX = 125
SYM_PHASING_RX = [111, 110, 109, 108, 107, 106, 105, 104]

# No information / wildcard
SYM_NO_INFO = 126
SYM_WILDCARD = 126

# Dot pattern length (Section 3.4)
DOT_PATTERN_BITS_VHF = 20
DOT_PATTERN_BITS_HF_MF = 200

# Phasing: 6 DX + 8 RX = 14 phasing characters total (Section 3.2)
PHASING_DX_COUNT = 6
PHASING_RX_SYMBOLS = [111, 110, 109, 108, 107, 106, 105, 104]

# Time diversity: 4 characters between DX and RX (Section 1.2.1)
TIME_DIVERSITY_SPREAD = 4

# VHF DSC physical parameters (Section 1.3.2)
VHF_MARK_HZ = 1300
VHF_SPACE_HZ = 2100
VHF_BAUD = 1200
VHF_CHANNEL_70_MHZ = 156.525

# Internal processing
INTERNAL_SAMPLE_RATE = 16000

# Distress coordinates: 10 digits (Section 8.1.2)
# Digit 1: quadrant (0=NE, 1=NW, 2=SE, 3=SW)
# Digits 2-3: latitude degrees (00-90)
# Digits 4-5: latitude minutes (00-59)
# Digits 6-8: longitude degrees (000-180)
# Digits 9-10: longitude minutes (00-59)
DISTRESS_COORD_DIGITS = 10

# Time: 4 digits (Section 8.1.3)
# Digits 1-2: hours (00-23)
# Digits 3-4: minutes (00-59)
TIME_DIGITS = 4

# MMSI: 9 digits transmitted as 5 character pairs (Section 5.2)
# (M,I)(D,X4)(X5,X6)(X7,X8)(X9,0)
MMSI_DIGITS = 9
MMSI_CHARS = 5

# ECC: even vertical parity of all information characters (Section 10.2)
# Format specifier and EOS count as info chars
# Phasing and RX chars do NOT count


class FormatSpecifier(IntEnum):
    DISTRESS = 112
    ALL_SHIPS = 116
    GROUP = 114
    INDIVIDUAL = 120
    GEO_AREA = 102
    INDIVIDUAL_AUTO = 123


class CategoryOfCall(IntEnum):
    DISTRESS = 112
    URGENCY = 110
    SAFETY = 108
    ROUTINE = 100


class NatureOfDistress(IntEnum):
    FIRE_EXPLOSION = 100
    FLOODING = 101
    COLLISION = 102
    GROUNDING = 103
    LISTING = 104
    SINKING = 105
    DISABLED_ADRIFT = 106
    UNDESIGNATED = 107
    ABANDONING_SHIP = 108
    PIRACY = 109
    MAN_OVERBOARD = 110


class FirstTelecommand(IntEnum):
    F3E_G3E_ALL_TP = 100
    F3E_G3E_DUPLEX_TP = 101
    POLLING = 103
    UNABLE_TO_COMPLY = 104
    END_OF_CALL = 105
    DATA = 106
    J3E_TP = 109
    DISTRESS_ACK = 110
    DISTRESS_RELAY = 112
    F1B_J2B_TTY_FEC = 113
    F1B_J2B_TTY_ARQ = 115
    TEST = 118
    SHIP_POS_UPDATE = 121


class SecondTelecommand(IntEnum):
    NO_INFO = 126
    NO_REASON = 100
    CONGESTION = 101
    BUSY = 102
    QUEUE = 103
    STATION_BARRED = 104
    NO_OPERATOR = 105
    OP_TEMP_UNAVAIL = 106
    EQUIP_DISABLED = 107
    UNABLE_CHANNEL = 108
    UNABLE_MODE = 109
    SHIPS_AIRCRAFT = 110
    MEDICAL = 111
    PAY_PHONE = 112
    FACSIMILE = 113


class EndOfSequence(IntEnum):
    ACK_RQ = 117
    ACK_BQ = 122
    EOT = 127
