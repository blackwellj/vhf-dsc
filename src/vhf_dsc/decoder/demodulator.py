"""DSC demodulator - converts audio to bit stream.

Handles real off-air signals with:
- Any sample rate
- Goertzel-based detection with sliding window
- Robust symbol synchronization
"""

from __future__ import annotations

import numpy as np

from ..protocol.constants import VHF_MARK_FREQ, VHF_SPACE_FREQ, VHF_BAUD_RATE
from ..dsp.goertzel import GoertzelDetector


class DSCDemodulator:
    """Demodulate DSC audio to raw bit stream using Goertzel detector."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.baud_rate = VHF_BAUD_RATE
        self.samples_per_symbol = sample_rate / VHF_BAUD_RATE

        # Use block size of 1 symbol duration for per-symbol detection
        block_size = max(8, int(round(self.samples_per_symbol)))
        self._detector = GoertzelDetector(
            sample_rate,
            [VHF_MARK_FREQ, VHF_SPACE_FREQ],
            block_size=block_size,
        )

    def demodulate(self, samples: np.ndarray) -> np.ndarray:
        """Demodulate audio samples to bits."""
        mags = self._detector.detect_stream(samples)

        bits = np.where(mags[:, 0] > mags[:, 1], 1, 0)

        return bits

    def demodulate_with_confidence(self, samples: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Demodulate with per-bit confidence values."""
        mags = self._detector.detect_stream(samples)

        bits = np.where(mags[:, 0] > mags[:, 1], 1, 0)

        total = mags[:, 0] + mags[:, 1]
        confidence = np.zeros(len(bits))
        mask = total > 1e-10
        confidence[mask] = np.abs(mags[mask, 0] - mags[mask, 1]) / total[mask]

        return bits, confidence
