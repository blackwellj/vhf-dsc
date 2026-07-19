"""Signal detector for DSC preamble detection."""

from __future__ import annotations

import numpy as np

from ..protocol.constants import GOERTZEL_THRESHOLD
from ..protocol.symbols import SYM_PHASING_DX, SYM_PHASING_RX
from ..dsp.goertzel import create_vhf_goertzel


class SignalDetector:
    """Detect DSC signal presence via phasing sequence detection."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.goertzel = create_vhf_goertzel(sample_rate)
        self._bit_buffer: list[int] = []
        self._max_buffer = 200

    def detect(self, samples: np.ndarray) -> tuple[bool, float]:
        """Check if DSC signal is present in samples."""
        magnitudes = self.goertzel.detect_stream(samples)
        if len(magnitudes) == 0:
            return False, 0.0

        bits = np.where(magnitudes[:, 0] > magnitudes[:, 1], 1, 0)
        self._bit_buffer.extend(bits.tolist())
        self._bit_buffer = self._bit_buffer[-self._max_buffer:]

        return self._check_phasing()

    def _check_phasing(self) -> tuple[bool, float]:
        """Check for phasing sequences in bit buffer."""
        if len(self._bit_buffer) < 40:
            return False, 0.0

        best_confidence = 0.0
        for i in range(len(self._bit_buffer) - 39):
            window = self._bit_buffer[i:i + 40]
            p1_match = self._match_sequence(window[:20], [1, 0])
            p2_match = self._match_sequence(window[20:40], [0, 1])
            confidence = (p1_match + p2_match) / 2.0
            if confidence > best_confidence:
                best_confidence = confidence

        return best_confidence > 0.7, best_confidence

    def _match_sequence(self, bits: list[int], pattern: list[int]) -> float:
        if len(bits) < len(pattern):
            return 0.0
        matches = sum(1 for b, p in zip(bits, pattern) if b == p)
        return matches / len(pattern)

    def detect_simple(self, samples: np.ndarray,
                      threshold: float = GOERTZEL_THRESHOLD) -> bool:
        """Simple energy-based detection."""
        magnitudes = self.goertzel.detect_stream(samples)
        if len(magnitudes) == 0:
            return False
        avg_signal = np.mean(np.max(magnitudes, axis=1))
        return avg_signal > threshold

    def reset(self):
        self._bit_buffer.clear()
