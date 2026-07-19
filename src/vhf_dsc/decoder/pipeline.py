"""Main DSC decoder pipeline orchestrator.

Handles real off-air signals with:
- Automatic signal detection (skips silence)
- Dot pattern detection with error tolerance
- Error-tolerant phasing detection
- Multiple bit alignment attempts
- ITU-compliant time diversity de-interleaving
- Character-level error correction using Hamming distance
- Multiple decode attempts with best result selection
"""

from __future__ import annotations

from typing import Callable, Optional

import numpy as np

from .demodulator import DSCDemodulator
from .parser import DSCParser
from .validator import DSCValidator
from .clusterer import MessageClusterer
from ..protocol.message import DSCMessage
from ..protocol.characters import bits_to_code, decode_char, CHARACTER_TABLE, REVERSE_TABLE
from ..protocol.symbols import SYM_PHASING_DX, SYM_PHASING_RX

# Time diversity spread per ITU-R M.493-16 Section 1.2.1
TIME_DIVERSITY_SPREAD = 4


class DSCDecoderPipeline:
    """Complete DSC decode pipeline for real off-air signals."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.demodulator = DSCDemodulator(sample_rate)
        self.parser = DSCParser()
        self.validator = DSCValidator()
        self.clusterer = MessageClusterer()

        self._on_message: Optional[Callable[[DSCMessage], None]] = None
        self._message_count = 0
        self._error_count = 0

    def process(self, samples: np.ndarray) -> list[DSCMessage]:
        """Process audio samples and decode all DSC messages found."""
        bits = self.demodulator.demodulate(samples)
        if len(bits) < 100:
            return []

        messages = self._search_for_messages(bits.tolist())

        return messages

    def _search_for_messages(self, bits: list[int]) -> list[DSCMessage]:
        """Search for DSC messages in a bit stream."""
        messages = []

        # Find all dot pattern positions
        dot_positions = self._find_all_dot_patterns(bits)

        if not dot_positions:
            return []

        # Try each dot position
        best_msg = None
        best_score = -1

        for dot_end in dot_positions:
            content_bits = bits[dot_end:]

            # Try both bit alignments
            for bit_offset in [0, 1]:
                bit_list = content_bits[bit_offset:]
                symbols = self._decode_symbols(bit_list)

                if len(symbols) < 10:
                    continue

                # Find phasing pattern
                phasing_positions = self._find_phasing_positions(symbols)

                for phasing_idx, match_score in phasing_positions:
                    content = symbols[phasing_idx + 14:]

                    if len(content) < 10:
                        continue

                    # Try multiple de-interleaving strategies
                    deinterleaved_streams = self._try_deinterleaving(content)

                    for dx_stream in deinterleaved_streams:
                        if len(dx_stream) < 10:
                            continue

                        msg = self.parser.parse(dx_stream)
                        msg.frequency_rx = self.sample_rate

                        score = self._score_message(msg, match_score)

                        if score > best_score:
                            best_score = score
                            best_msg = msg

        if best_msg is not None:
            is_valid, errors = self.validator.validate(best_msg)
            if not is_valid:
                best_msg.status = f"VALIDATION_ERROR: {', '.join(errors)}"
                self._error_count += 1

            best = self.clusterer.add(best_msg)
            if best is not None:
                messages.append(best)
                self._message_count += 1

                if self._on_message:
                    self._on_message(best)

        return messages

    def _try_deinterleaving(self, content: list[int]) -> list[list[int]]:
        """Try multiple de-interleaving strategies."""
        streams = []
        n = len(content) // 2
        if n < 10:
            return streams

        # Strategy 1: ITU-compliant de-interleaving
        # diverse has 2*n symbols, where n is the original message length
        # DX = content[0:spread+1] + content[spread+2::2][:n-(spread+1)]
        dx1 = list(content[:TIME_DIVERSITY_SPREAD + 1])
        dx1.extend(content[TIME_DIVERSITY_SPREAD + 2::2][:n - (TIME_DIVERSITY_SPREAD + 1)])
        streams.append(dx1)

        # Strategy 2: Simple alternating (even positions)
        dx2 = content[0::2]
        if len(dx2) >= 10:
            streams.append(dx2)

        # Strategy 3: Simple alternating (odd positions)
        dx3 = content[1::2]
        if len(dx3) >= 10:
            streams.append(dx3)

        # Strategy 4: ITU-compliant with offset 1
        if len(content) >= TIME_DIVERSITY_SPREAD + 3:
            dx4 = list(content[1:TIME_DIVERSITY_SPREAD + 2])
            dx4.extend(content[TIME_DIVERSITY_SPREAD + 3::2][:n - (TIME_DIVERSITY_SPREAD + 1)])
            if len(dx4) >= 10:
                streams.append(dx4)

        return streams

    def _find_all_dot_patterns(self, bits: list[int]) -> list[int]:
        """Find all dot pattern positions in the bit stream."""
        dot_ends = []

        for start in [0, 1]:
            expected = np.array([(i + start) % 2 for i in range(20)])
            for i in range(0, len(bits) - 20, 10):
                window = np.array(bits[i:i + 20])
                match = np.sum(window == expected)
                if match >= 16:
                    dot_end = i + 20
                    while dot_end < len(bits) and bits[dot_end] == expected[(dot_end - i) % 2]:
                        dot_end += 1
                    dot_ends.append(dot_end)

        dot_ends = sorted(set(dot_ends))
        return dot_ends

    def _decode_symbols(self, bits: list[int]) -> list[int]:
        """Decode bits to symbols with error correction."""
        symbols = []
        temp = list(bits)
        while len(temp) >= 10:
            char_bits = temp[:10]
            temp = temp[10:]
            code = bits_to_code(char_bits)
            sym = decode_char(code)
            if sym >= 0:
                symbols.append(sym)
            else:
                # Try error correction: find closest valid code
                best_sym = -1
                best_dist = 11
                for valid_code, valid_sym in REVERSE_TABLE.items():
                    dist = bin(code ^ valid_code).count("1")
                    if dist < best_dist:
                        best_dist = dist
                        best_sym = valid_sym
                if best_dist <= 2 and best_sym >= 0:
                    symbols.append(best_sym)
        return symbols

    def _find_phasing_positions(self, symbols: list[int]) -> list[tuple[int, int]]:
        """Find phasing pattern positions in symbol stream."""
        results = []
        phasing_symbols_set = {SYM_PHASING_DX} | set(SYM_PHASING_RX)

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

            if matches >= 13:
                results.append((i, matches))

        return results

    def _score_message(self, msg: DSCMessage, phasing_matches: int) -> int:
        """Score a decoded message to select the best decode."""
        score = 0

        # Valid format specifiers get highest priority
        valid_formats = {112, 116, 114, 120, 102}
        if msg.format_specifier in valid_formats:
            score += 200
        else:
            return 0  # Invalid format, skip

        # Valid categories
        valid_categories = {100, 108, 110, 112}
        if msg.category in valid_categories:
            score += 100

        # Valid MMSI
        if msg.mmsi_self and len(msg.mmsi_self) == 9:
            score += 80

        # ECC validation
        is_valid, _ = self.validator.validate(msg)
        if is_valid:
            score += 150

        # Phasing match quality
        score += phasing_matches * 20

        return score

    def process_stream(self, samples: np.ndarray,
                       chunk_size: int = 48000) -> list[DSCMessage]:
        """Process a continuous stream in chunks."""
        all_messages = []
        for i in range(0, len(samples), chunk_size):
            chunk = samples[i:i + chunk_size]
            if len(chunk) < chunk_size:
                chunk = samples[i:]

            messages = self.process(chunk)
            all_messages.extend(messages)

        return all_messages

    def on_message(self, callback: Callable[[DSCMessage], None]):
        """Register a callback for decoded messages."""
        self._on_message = callback

    @property
    def message_count(self) -> int:
        return self._message_count

    @property
    def error_count(self) -> int:
        return self._error_count

    def reset(self):
        """Reset all pipeline state."""
        self.clusterer.reset()
        self._message_count = 0
        self._error_count = 0
