"""DSC serializer - converts DSCMessage to ITU-R M.493-16 compliant symbol stream.

Call sequence structure (Section 2):
1. Dot pattern (raw alternating bits)
2. Phasing sequence (symbol numbers)
3. Call content (DX/RX interleaved symbols)
4. Closing sequence (EOS + ECC + EOS)

Time diversity (Section 1.2.1): Each character transmitted twice with 4 chars between.
VHF: 33.3ms diversity interval (4 chars at 1200 baud)
"""

from __future__ import annotations

from ..protocol.message import DSCMessage
from ..protocol.symbols import (
    SYM_DISTRESS, SYM_ALL_SHIPS, SYM_GROUP, SYM_INDIVIDUAL,
    SYM_GEO_AREA, SYM_INDIVIDUAL_AUTO,
    SYM_CAT_DISTRESS, SYM_CAT_URGENCY, SYM_CAT_SAFETY, SYM_CAT_ROUTINE,
    SYM_NATURE_FIRE, SYM_NATURE_FLOODING, SYM_NATURE_COLLISION,
    SYM_NATURE_GROUNDING, SYM_NATURE_LISTING, SYM_NATURE_SINKING,
    SYM_NATURE_DISABLED, SYM_NATURE_UNDESIGNATED, SYM_NATURE_ABANDONING,
    SYM_NATURE_PIRACY, SYM_NATURE_MAN_OVERBOARD,
    SYM_TC1_F3E_G3E_ALL, SYM_TC1_DISTRESS_ACK, SYM_TC1_DISTRESS_RELAY,
    SYM_TC1_TEST,
    SYM_TC2_NO_INFO,
    SYM_EOS_ACK_RQ, SYM_EOS_ACK_BQ, SYM_EOS_EOT,
    SYM_PHASING_DX, SYM_PHASING_RX,
    SYM_NO_INFO,
    DOT_PATTERN_BITS_VHF, DOT_PATTERN_BITS_HF_MF,
    TIME_DIVERSITY_SPREAD,
)
from ..protocol.error_correction import compute_ecc, extract_info_symbols
from ..protocol.position import encode_position, encode_time_utc
from ..protocol.mmsi import MMSI
from ..protocol.constants import VHF_BAUD_RATE


class DSCSerializer:
    """Serialize DSCMessage to ITU-R M.493-16 compliant symbol stream."""

    def _build_info_symbols(self, msg: DSCMessage) -> list[int]:
        """Build the information symbol sequence (without preamble/phasing/EOS/ECC).

        This produces the DX stream symbols only.
        """
        symbols = []

        if msg.format_specifier == SYM_DISTRESS:
            symbols = self._build_distress(msg)
        elif msg.format_specifier == SYM_ALL_SHIPS:
            symbols = self._build_all_ships(msg)
        elif msg.format_specifier == SYM_INDIVIDUAL:
            symbols = self._build_individual(msg)
        elif msg.format_specifier == SYM_GROUP:
            symbols = self._build_group(msg)
        elif msg.format_specifier == SYM_GEO_AREA:
            symbols = self._build_geo_area(msg)
        elif msg.format_specifier == SYM_INDIVIDUAL_AUTO:
            symbols = self._build_individual_auto(msg)
        elif msg.format_specifier == 112 and msg.category == SYM_CAT_DISTRESS:
            symbols = self._build_distress_ack(msg)
        else:
            symbols = self._build_test(msg)

        return symbols

    def _build_distress(self, msg: DSCMessage) -> list[int]:
        """Build distress alert (Table A1-4.1).
        Format: Self-ID(5) + Nature(1) + Coordinates(5) + Time(2) + TC1(1) + TC2(1)
        Note: No category for distress alerts (Section 6.1)
        """
        symbols = []

        symbols.append(SYM_DISTRESS)

        if msg.mmsi_self:
            mmsi = MMSI(msg.mmsi_self)
            symbols.extend(mmsi.to_symbol_chars())
        else:
            symbols.extend([SYM_NO_INFO] * 5)

        nature = msg.nature_of_distress or SYM_NATURE_UNDESIGNATED
        symbols.append(nature)

        if msg.position and msg.position.is_valid:
            pos_digits = encode_position(msg.position.latitude, msg.position.longitude)
            pos_chars = self._digits_to_chars(pos_digits)
            symbols.extend(pos_chars)
        else:
            symbols.extend([99] * 5)

        time_str = msg.time_utc or "8888"
        time_digits = encode_time_utc(time_str)
        time_chars = self._digits_to_chars(time_digits)
        symbols.extend(time_chars)

        symbols.append(msg.telecommand_1 or SYM_TC1_F3E_G3E_ALL)
        symbols.append(msg.telecommand_2 or SYM_TC2_NO_INFO)

        return symbols

    def _build_all_ships(self, msg: DSCMessage) -> list[int]:
        """Build all-ships call (Table A1-4.5).
        Format: Category(1) + Self-ID(5) + TC1(1) + TC2(1) + Freq(6)
        """
        symbols = []
        symbols.append(SYM_ALL_SHIPS)
        symbols.append(msg.category or SYM_CAT_SAFETY)
        symbols.append(SYM_NO_INFO)

        if msg.mmsi_self:
            mmsi = MMSI(msg.mmsi_self)
            symbols.extend(mmsi.to_symbol_chars())
        else:
            symbols.extend([SYM_NO_INFO] * 5)

        symbols.append(msg.telecommand_1 or SYM_TC2_NO_INFO)
        symbols.append(msg.telecommand_2 or SYM_TC2_NO_INFO)
        symbols.extend([SYM_NO_INFO] * 6)

        return symbols

    def _build_individual(self, msg: DSCMessage) -> list[int]:
        """Build individual call (Table A1-4.5).
        Format: Category(1) + Address(5) + Self-ID(5) + TC1(1) + TC2(1) + Freq(6)
        """
        symbols = []
        symbols.append(SYM_INDIVIDUAL)
        symbols.append(msg.category or SYM_CAT_ROUTINE)

        if msg.mmsi_dest:
            mmsi = MMSI(msg.mmsi_dest)
            symbols.extend(mmsi.to_symbol_chars())
        else:
            symbols.extend([SYM_NO_INFO] * 5)

        if msg.mmsi_self:
            mmsi = MMSI(msg.mmsi_self)
            symbols.extend(mmsi.to_symbol_chars())
        else:
            symbols.extend([SYM_NO_INFO] * 5)

        symbols.append(msg.telecommand_1 or SYM_TC2_NO_INFO)
        symbols.append(msg.telecommand_2 or SYM_TC2_NO_INFO)
        symbols.extend([SYM_NO_INFO] * 6)

        return symbols

    def _build_group(self, msg: DSCMessage) -> list[int]:
        """Build group call (Table A1-4.6).
        Format: Category(1) + Address(5) + Self-ID(5) + TC1(1) + TC2(1) + Freq(6)
        """
        symbols = []
        symbols.append(SYM_GROUP)
        symbols.append(msg.category or SYM_CAT_ROUTINE)

        if msg.mmsi_dest:
            mmsi = MMSI(msg.mmsi_dest)
            symbols.extend(mmsi.to_symbol_chars())
        else:
            symbols.extend([SYM_NO_INFO] * 5)

        if msg.mmsi_self:
            mmsi = MMSI(msg.mmsi_self)
            symbols.extend(mmsi.to_symbol_chars())
        else:
            symbols.extend([SYM_NO_INFO] * 5)

        symbols.append(msg.telecommand_1 or SYM_TC2_NO_INFO)
        symbols.append(msg.telecommand_2 or SYM_TC2_NO_INFO)
        symbols.extend([SYM_NO_INFO] * 6)

        return symbols

    def _build_geo_area(self, msg: DSCMessage) -> list[int]:
        """Build geographic area call (Table A1-4.7).
        Format: Category(1) + Geo-Address(5) + Self-ID(5) + TC1(1) + TC2(1) + Freq(6)
        """
        symbols = []
        symbols.append(SYM_GEO_AREA)
        symbols.append(msg.category or SYM_CAT_SAFETY)

        if msg.mmsi_dest:
            mmsi = MMSI(msg.mmsi_dest)
            symbols.extend(mmsi.to_symbol_chars())
        else:
            symbols.extend([SYM_NO_INFO] * 5)

        if msg.mmsi_self:
            mmsi = MMSI(msg.mmsi_self)
            symbols.extend(mmsi.to_symbol_chars())
        else:
            symbols.extend([SYM_NO_INFO] * 5)

        symbols.append(msg.telecommand_1 or SYM_TC2_NO_INFO)
        symbols.append(msg.telecommand_2 or SYM_TC2_NO_INFO)
        symbols.extend([SYM_NO_INFO] * 6)

        return symbols

    def _build_individual_auto(self, msg: DSCMessage) -> list[int]:
        """Build individual auto service call (Table A1-4.10.1)."""
        symbols = []
        symbols.append(SYM_INDIVIDUAL_AUTO)
        symbols.append(msg.category or SYM_CAT_ROUTINE)

        if msg.mmsi_dest:
            mmsi = MMSI(msg.mmsi_dest)
            symbols.extend(mmsi.to_symbol_chars())
        else:
            symbols.extend([SYM_NO_INFO] * 5)

        if msg.mmsi_self:
            mmsi = MMSI(msg.mmsi_self)
            symbols.extend(mmsi.to_symbol_chars())
        else:
            symbols.extend([SYM_NO_INFO] * 5)

        symbols.append(msg.telecommand_1 or SYM_TC2_NO_INFO)
        symbols.append(msg.telecommand_2 or SYM_TC2_NO_INFO)
        symbols.extend([SYM_NO_INFO] * 6)

        return symbols

    def _build_distress_ack(self, msg: DSCMessage) -> list[int]:
        """Build distress acknowledgement (Table A1-4.2).
        Format: Category(112) + Self-ID(5) + TC1(1) + TC2(1) + Distress-ID(5) + Nature(1) + Coords(5) + Time(2) + TC1(1)
        """
        symbols = []
        symbols.append(SYM_DISTRESS)
        symbols.append(SYM_CAT_DISTRESS)

        if msg.mmsi_self:
            mmsi = MMSI(msg.mmsi_self)
            symbols.extend(mmsi.to_symbol_chars())
        else:
            symbols.extend([SYM_NO_INFO] * 5)

        symbols.append(msg.telecommand_1 or SYM_TC1_DISTRESS_ACK)
        symbols.append(msg.telecommand_2 or SYM_TC1_DISTRESS_ACK)

        if msg.distress_id or msg.mmsi_dest:
            mmsi = MMSI(msg.distress_id or msg.mmsi_dest)
            symbols.extend(mmsi.to_symbol_chars())
        else:
            symbols.extend([SYM_NO_INFO] * 5)

        nature = msg.nature_of_distress or SYM_NATURE_UNDESIGNATED
        symbols.append(nature)

        if msg.position and msg.position.is_valid:
            pos_digits = encode_position(msg.position.latitude, msg.position.longitude)
            pos_chars = self._digits_to_chars(pos_digits)
            symbols.extend(pos_chars)
        else:
            symbols.extend([99] * 5)

        time_str = msg.time_utc or "8888"
        time_digits = encode_time_utc(time_str)
        time_chars = self._digits_to_chars(time_digits)
        symbols.extend(time_chars)

        symbols.append(msg.telecommand_1 or SYM_TC1_F3E_G3E_ALL)

        return symbols

    def _build_test(self, msg: DSCMessage) -> list[int]:
        """Build test call (Table A1-4.7)."""
        symbols = []
        symbols.append(SYM_INDIVIDUAL)
        symbols.append(SYM_CAT_ROUTINE)
        symbols.append(SYM_NO_INFO)

        if msg.mmsi_self:
            mmsi = MMSI(msg.mmsi_self)
            symbols.extend(mmsi.to_symbol_chars())
        else:
            symbols.extend([SYM_NO_INFO] * 5)

        symbols.append(SYM_TC1_TEST)
        symbols.append(SYM_TC2_NO_INFO)
        symbols.extend([SYM_NO_INFO] * 6)

        return symbols

    def _digits_to_chars(self, digits: list[int]) -> list[int]:
        """Pack digit pairs into symbol numbers per Table A1-2."""
        chars = []
        for i in range(0, len(digits), 2):
            val = digits[i] * 10 + digits[i + 1]
            chars.append(val)
        return chars

    def _apply_time_diversity(self, symbols: list[int]) -> list[int]:
        """Apply time diversity: interleave DX and RX with 4-char spread.

        For VHF: 4 chars between DX and RX = 33.3ms
        Transmitted order: DX[0], DX[1], DX[2], DX[3], DX[4],
                          RX[0], DX[5], RX[1], DX[6], RX[2], ...
        """
        n = len(symbols)
        if n <= TIME_DIVERSITY_SPREAD:
            return symbols + symbols

        result = []
        for i in range(n):
            result.append(symbols[i])
            if i >= TIME_DIVERSITY_SPREAD:
                result.append(symbols[i - TIME_DIVERSITY_SPREAD])

        for i in range(n - TIME_DIVERSITY_SPREAD, n):
            result.append(symbols[i])

        return result

    def serialize(self, msg: DSCMessage) -> list[int]:
        """Serialize DSCMessage to complete symbol stream with diversity.

        Returns list of symbol numbers (not 10-bit codes).
        """
        info_symbols = self._build_info_symbols(msg)

        eos = msg.eos or SYM_EOS_EOT

        ecc_symbols = extract_info_symbols(info_symbols)
        ecc_symbols.append(eos)
        ecc = compute_ecc(ecc_symbols)

        call_symbols = list(info_symbols)
        call_symbols.append(eos)
        call_symbols.append(ecc)
        call_symbols.append(eos)

        diverse_symbols = self._apply_time_diversity(call_symbols)

        return diverse_symbols

    def serialize_to_bits(self, msg: DSCMessage) -> list[int]:
        """Serialize to raw bit stream including dot pattern and phasing.

        Returns list of bits (0 or 1).
        """
        from ..protocol.characters import code_to_bits

        bits = []

        for _ in range(DOT_PATTERN_BITS_VHF):
            bits.append(len(bits) % 2)

        bits.extend(code_to_bits(125))
        for sym in SYM_PHASING_RX:
            bits.extend(code_to_bits(sym))
        for _ in range(5):
            bits.extend(code_to_bits(125))

        symbols = self.serialize(msg)
        for sym in symbols:
            from ..protocol.characters import encode_char
            code = encode_char(sym)
            bits.extend(code_to_bits(code))

        return bits
