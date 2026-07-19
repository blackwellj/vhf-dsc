"""DSC framer - converts bit stream to symbol numbers.

Handles real-world noisy signals with:
- Error-tolerant phasing detection
- Multiple bit alignment attempts
- Time diversity de-interleaving
"""

from __future__ import annotations

from ..protocol.characters import bits_to_code, decode_char
from ..protocol.symbols import SYM_PHASING_DX, SYM_PHASING_RX

# Time diversity spread per ITU-R M.493-16 Section 1.2.1
TIME_DIVERSITY_SPREAD = 4


class DSCFramer:
    """Frame a raw bit stream into symbol numbers."""

    def __init__(self):
        self._bit_buffer: list[int] = []
        self._phasing_found = False
        self._bit_offset = 0

    def feed(self, bits: list[int]) -> list[int]:
        """Feed bits and extract complete symbols."""
        self._bit_buffer.extend(bits)
        symbols = []

        while len(self._bit_buffer) >= 10:
            char_bits = self._bit_buffer[:10]
            self._bit_buffer = self._bit_buffer[10:]

            code = bits_to_code(char_bits)
            sym = decode_char(code)
            if sym >= 0:
                symbols.append(sym)

        return symbols

    def feed_and_frame(self, bits: list[int]) -> tuple[list[int], bool]:
        """Feed bits, detect phasing, de-interleave, and return call content symbols."""
        self._bit_buffer.extend(bits)

        if not self._phasing_found:
            self._phasing_found, self._bit_offset = self._search_and_strip_phasing()

        symbols = []
        while len(self._bit_buffer) >= 10:
            char_bits = self._bit_buffer[:10]
            self._bit_buffer = self._bit_buffer[10:]

            code = bits_to_code(char_bits)
            sym = decode_char(code)
            if sym >= 0:
                symbols.append(sym)

        if self._phasing_found and symbols:
            symbols = self._deinterleave(symbols)

        return symbols, self._phasing_found

    def find_phasing_positions(self, bits: list[int]) -> list[tuple[int, int, int]]:
        """Find all possible phasing positions in a bit stream.

        Returns list of (bit_offset, phasing_symbol_index, match_score) tuples.
        """
        results = []
        phasing_symbols_set = {SYM_PHASING_DX} | set(SYM_PHASING_RX)

        # Try both bit alignments
        for bit_offset in [0, 1]:
            temp_bits = bits[bit_offset:]
            symbols = []
            temp = list(temp_bits)
            while len(temp) >= 10:
                char_bits = temp[:10]
                temp = temp[10:]
                code = bits_to_code(char_bits)
                sym = decode_char(code)
                if sym >= 0:
                    symbols.append(sym)

            # Search for phasing patterns with error tolerance
            for i in range(len(symbols) - 13):
                window = symbols[i:i + 14]
                matches = 0
                for j in range(14):
                    if j % 2 == 0:
                        if window[j] == SYM_PHASING_DX:
                            matches += 1
                    else:
                        if window[j] in phasing_symbols_set:
                            matches += 1

                if matches >= 10:  # At least 10/14 matches
                    results.append((bit_offset, i, matches))

        return results

    def _search_and_strip_phasing(self) -> tuple[bool, int]:
        """Search for phasing sequence and strip preamble + phasing from buffer."""
        if len(self._bit_buffer) < 140:
            return False, 0

        phasing_symbols_set = {SYM_PHASING_DX} | set(SYM_PHASING_RX)

        for bit_offset in [0, 1]:
            temp_buffer = list(self._bit_buffer[bit_offset:])
            decoded = []
            while len(temp_buffer) >= 10:
                char_bits = temp_buffer[:10]
                temp_buffer = temp_buffer[10:]
                code = bits_to_code(char_bits)
                sym = decode_char(code)
                if sym >= 0:
                    decoded.append(sym)

            # Search for phasing with error tolerance
            for i in range(len(decoded) - 13):
                window = decoded[i:i + 14]
                matches = 0
                for j in range(14):
                    if j % 2 == 0:
                        if window[j] == SYM_PHASING_DX:
                            matches += 1
                    else:
                        if window[j] in phasing_symbols_set:
                            matches += 1

                if matches >= 13:  # At least 13/14 matches
                    # Skip phasing symbols (14 symbols = 140 bits)
                    chars_to_skip = i + 14
                    bits_to_skip = bit_offset + chars_to_skip * 10
                    self._bit_buffer = self._bit_buffer[bits_to_skip:]
                    return True, bit_offset

        return False, 0

    def _deinterleave(self, symbols: list[int]) -> list[int]:
        """De-interleave time-diversity symbol stream.

        Per ITU-R M.493-16 Section 1.2.1:
        diverse has 2*n symbols, where n is the original message length
        DX = diverse[0:spread+1] + diverse[spread+2::2][:n-(spread+1)]
        """
        if len(symbols) < 10:
            return symbols

        n = len(symbols) // 2
        if n < 10:
            return symbols

        dx_stream = list(symbols[:TIME_DIVERSITY_SPREAD + 1])
        dx_stream.extend(symbols[TIME_DIVERSITY_SPREAD + 2::2][:n - (TIME_DIVERSITY_SPREAD + 1)])

        return dx_stream

    def reset(self):
        self._bit_buffer.clear()
        self._phasing_found = False
        self._bit_offset = 0
