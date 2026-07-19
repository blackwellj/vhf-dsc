"""DSC parser - converts symbol stream to DSCMessage per ITU-R M.493-16."""

from __future__ import annotations

from datetime import datetime

from ..protocol.message import DSCMessage
from ..protocol.position import Position, decode_position, decode_time_utc
from ..protocol.mmsi import MMSI
from ..protocol.symbols import (
    SYM_DISTRESS, SYM_ALL_SHIPS, SYM_GROUP, SYM_INDIVIDUAL,
    SYM_GEO_AREA, SYM_INDIVIDUAL_AUTO,
    SYM_CAT_DISTRESS, SYM_CAT_URGENCY, SYM_CAT_SAFETY, SYM_CAT_ROUTINE,
    SYM_EOS_ACK_RQ, SYM_EOS_ACK_BQ, SYM_EOS_EOT,
    SYM_NO_INFO,
)


class DSCParser:
    """Parse DSC symbol stream into structured DSCMessage."""

    def parse(self, symbols: list[int]) -> DSCMessage:
        """Parse a list of symbol numbers into a DSCMessage.

        Args:
            symbols: List of symbol numbers (DX stream after de-interleaving)

        Returns:
            Parsed DSCMessage
        """
        msg = DSCMessage()
        msg.raw_symbols = list(symbols)
        msg.timestamp = datetime.utcnow()

        if len(symbols) < 2:
            msg.status = "TOO_SHORT"
            return msg

        idx = 0

        # Format specifier
        if idx < len(symbols):
            msg.format_specifier = symbols[idx]
            idx += 1

        # Parse based on format
        if msg.format_specifier == SYM_DISTRESS:
            self._parse_distress(msg, symbols, idx)
        elif msg.format_specifier == SYM_ALL_SHIPS:
            self._parse_all_ships(msg, symbols, idx)
        elif msg.format_specifier in (SYM_INDIVIDUAL, SYM_INDIVIDUAL_AUTO):
            self._parse_individual(msg, symbols, idx)
        elif msg.format_specifier == SYM_GROUP:
            self._parse_group(msg, symbols, idx)
        elif msg.format_specifier == SYM_GEO_AREA:
            self._parse_geo_area(msg, symbols, idx)
        else:
            msg.status = f"UNKNOWN_FORMAT: {msg.format_specifier}"
            return msg

        msg.status = msg.status or "OK"
        return msg

    def _parse_distress(self, msg: DSCMessage, symbols: list[int], idx: int):
        """Parse distress alert (Table A1-4.1).
        Format: Self-ID(5) + Nature(1) + Coords(5) + Time(2) + TC1(1) + TC2(1)
        Note: No category for distress alerts (Section 6.1)
        """
        if idx + 15 > len(symbols):
            msg.status = "INCOMPLETE"
            return

        # Self-ID (5 symbols)
        if idx + 5 <= len(symbols):
            mmsi_chars = symbols[idx:idx+5]
            msg.mmsi_self = self._decode_mmsi(mmsi_chars)
            idx += 5

        # Nature of distress (1 symbol)
        if idx < len(symbols):
            msg.nature_of_distress = symbols[idx]
            idx += 1

        # Coordinates (5 symbols)
        if idx + 5 <= len(symbols):
            pos_chars = symbols[idx:idx+5]
            pos = self._decode_position(pos_chars)
            msg.position = pos
            idx += 5

        # Time (2 symbols)
        if idx + 2 <= len(symbols):
            time_chars = symbols[idx:idx+2]
            msg.time_utc = self._decode_time(time_chars)
            idx += 2

        # TC1 (1 symbol)
        if idx < len(symbols):
            msg.telecommand_1 = symbols[idx]
            idx += 1

        # TC2 (1 symbol)
        if idx < len(symbols):
            msg.telecommand_2 = symbols[idx]
            idx += 1

        # EOS (1 symbol)
        if idx < len(symbols) and symbols[idx] in (117, 122, 127):
            msg.eos = symbols[idx]
            idx += 1

        # ECC (1 symbol)
        if idx < len(symbols):
            msg.ecc = symbols[idx]

    def _parse_all_ships(self, msg: DSCMessage, symbols: list[int], idx: int):
        """Parse all-ships call (Table A1-4.5).
        Format: Category(1) + Self-ID(5) + TC1(1) + TC2(1) + Freq(6)
        """
        if idx < len(symbols):
            msg.category = symbols[idx]
            idx += 1

        if idx + 5 <= len(symbols):
            mmsi_chars = symbols[idx:idx+5]
            msg.mmsi_self = self._decode_mmsi(mmsi_chars)
            idx += 5

        if idx < len(symbols):
            msg.telecommand_1 = symbols[idx]
            idx += 1

        if idx < len(symbols):
            msg.telecommand_2 = symbols[idx]
            idx += 1

        # Skip frequency (6 symbols)
        idx += 6

        # EOS
        if idx < len(symbols) and symbols[idx] in (117, 122, 127):
            msg.eos = symbols[idx]
            idx += 1

        # ECC
        if idx < len(symbols):
            msg.ecc = symbols[idx]

    def _parse_individual(self, msg: DSCMessage, symbols: list[int], idx: int):
        """Parse individual call (Table A1-4.5).
        Format: Category(1) + Address(5) + Self-ID(5) + TC1(1) + TC2(1) + Freq(6)
        """
        if idx < len(symbols):
            msg.category = symbols[idx]
            idx += 1

        if idx + 5 <= len(symbols):
            mmsi_chars = symbols[idx:idx+5]
            msg.mmsi_dest = self._decode_mmsi(mmsi_chars)
            idx += 5

        if idx + 5 <= len(symbols):
            mmsi_chars = symbols[idx:idx+5]
            msg.mmsi_self = self._decode_mmsi(mmsi_chars)
            idx += 5

        if idx < len(symbols):
            msg.telecommand_1 = symbols[idx]
            idx += 1

        if idx < len(symbols):
            msg.telecommand_2 = symbols[idx]
            idx += 1

        # Skip frequency (6 symbols)
        idx += 6

        # EOS
        if idx < len(symbols) and symbols[idx] in (117, 122, 127):
            msg.eos = symbols[idx]
            idx += 1

        # ECC
        if idx < len(symbols):
            msg.ecc = symbols[idx]

    def _parse_group(self, msg: DSCMessage, symbols: list[int], idx: int):
        """Parse group call (Table A1-4.6)."""
        if idx < len(symbols):
            msg.category = symbols[idx]
            idx += 1

        if idx + 5 <= len(symbols):
            mmsi_chars = symbols[idx:idx+5]
            msg.mmsi_dest = self._decode_mmsi(mmsi_chars)
            idx += 5

        if idx + 5 <= len(symbols):
            mmsi_chars = symbols[idx:idx+5]
            msg.mmsi_self = self._decode_mmsi(mmsi_chars)
            idx += 5

        if idx < len(symbols):
            msg.telecommand_1 = symbols[idx]
            idx += 1

        if idx < len(symbols):
            msg.telecommand_2 = symbols[idx]
            idx += 1

        idx += 6  # Freq

        if idx < len(symbols) and symbols[idx] in (117, 122, 127):
            msg.eos = symbols[idx]
            idx += 1

        if idx < len(symbols):
            msg.ecc = symbols[idx]

    def _parse_geo_area(self, msg: DSCMessage, symbols: list[int], idx: int):
        """Parse geographic area call (Table A1-4.7)."""
        if idx < len(symbols):
            msg.category = symbols[idx]
            idx += 1

        if idx + 5 <= len(symbols):
            mmsi_chars = symbols[idx:idx+5]
            msg.mmsi_dest = self._decode_mmsi(mmsi_chars)
            idx += 5

        if idx + 5 <= len(symbols):
            mmsi_chars = symbols[idx:idx+5]
            msg.mmsi_self = self._decode_mmsi(mmsi_chars)
            idx += 5

        if idx < len(symbols):
            msg.telecommand_1 = symbols[idx]
            idx += 1

        if idx < len(symbols):
            msg.telecommand_2 = symbols[idx]
            idx += 1

        idx += 6  # Freq

        if idx < len(symbols) and symbols[idx] in (117, 122, 127):
            msg.eos = symbols[idx]
            idx += 1

        if idx < len(symbols):
            msg.ecc = symbols[idx]

    def _decode_mmsi(self, chars: list[int]) -> str:
        """Decode MMSI from 5 symbol numbers.

        Each symbol number represents a pair of digits (00-99).
        MMSI is 9 digits: (M,I)(D,X4)(X5,X6)(X7,X8)(X9,0)
        """
        if len(chars) < 5:
            return ""

        digits = []
        for ch in chars[:4]:
            if 0 <= ch <= 99:
                digits.append((ch // 10) % 10)
                digits.append(ch % 10)
            else:
                return ""

        # Last symbol: only first digit counts (X9), second digit should be 0
        last_ch = chars[4]
        if 0 <= last_ch <= 99:
            digits.append((last_ch // 10) % 10)

        if len(digits) >= 9:
            return "".join(str(d) for d in digits[:9])
        return ""

    def _decode_position(self, chars: list[int]) -> Position:
        """Decode position from 5 symbol numbers.

        Format: Quadrant(1) + Lat(2) + Lon(3)
        """
        if len(chars) < 5:
            return Position()

        # Extract digits
        digits = []
        for ch in chars:
            if 0 <= ch <= 99:
                digits.append((ch // 10) % 10)
                digits.append(ch % 10)
            else:
                return Position()

        if len(digits) < 10:
            return Position()

        # Quadrant
        quadrant = digits[0]
        lat_deg = digits[1] * 10 + digits[2]
        lat_min = digits[3] * 10 + digits[4]
        lon_deg = digits[5] * 100 + digits[6] * 10 + digits[7]
        lon_min = digits[8] * 10 + digits[9]

        lat = lat_deg + lat_min / 60.0
        lon = lon_deg + lon_min / 60.0

        if quadrant & 2:
            lat = -lat
        if quadrant & 1:
            lon = -lon

        return Position(latitude=lat, longitude=lon)

    def _decode_time(self, chars: list[int]) -> str:
        """Decode time from 2 symbol numbers."""
        if len(chars) < 2:
            return ""

        digits = []
        for ch in chars:
            if 0 <= ch <= 99:
                digits.append((ch // 10) % 10)
                digits.append(ch % 10)
            else:
                return ""

        if len(digits) >= 4:
            return f"{digits[0]}{digits[1]}{digits[2]}{digits[3]}"
        return ""
