"""Goertzel algorithm for tone detection.

Optimized for detecting the two VHF DSC frequencies:
- Mark: 1300 Hz
- Space: 2100 Hz
"""

from __future__ import annotations

import numpy as np


class GoertzelDetector:
    """Goertzel filter for detecting specific frequencies in audio."""

    def __init__(self, sample_rate: int, target_freqs: list[float],
                 block_size: int = None):
        self.sample_rate = sample_rate
        self.target_freqs = target_freqs

        if block_size is None:
            block_size = max(8, int(round(sample_rate / 1200)))

        self.block_size = block_size

        self._coeffs = []
        for freq in target_freqs:
            omega = 2.0 * np.pi * freq / sample_rate
            self._coeffs.append(2.0 * np.cos(omega))

    def detect(self, samples: np.ndarray) -> np.ndarray:
        """Run Goertzel detection on a block of samples."""
        if len(samples) != self.block_size:
            raise ValueError(f"Expected {self.block_size} samples, got {len(samples)}")

        magnitudes = np.zeros(len(self.target_freqs))

        for i, coeff in enumerate(self._coeffs):
            s_prev = 0.0
            s_prev2 = 0.0

            for sample in samples:
                s = sample + coeff * s_prev - s_prev2
                s_prev2 = s_prev
                s_prev = s

            power = s_prev2 * s_prev2 + s_prev * s_prev - coeff * s_prev * s_prev2
            magnitudes[i] = np.sqrt(power)

        return magnitudes

    def detect_stream(self, samples: np.ndarray) -> np.ndarray:
        """Run detection on a stream of samples in non-overlapping blocks."""
        if len(samples) % self.block_size != 0:
            samples = samples[:len(samples) - len(samples) % self.block_size]

        num_blocks = len(samples) // self.block_size
        result = np.zeros((num_blocks, len(self.target_freqs)))

        for i in range(num_blocks):
            block = samples[i * self.block_size:(i + 1) * self.block_size]
            result[i] = self.detect(block)

        return result

    def detect_sliding(self, samples: np.ndarray, hop: int = 1) -> np.ndarray:
        """Run detection with a sliding window for fine-grained analysis."""
        num_windows = (len(samples) - self.block_size) // hop + 1
        if num_windows < 1:
            return np.zeros((0, len(self.target_freqs)))

        result = np.zeros((num_windows, len(self.target_freqs)))

        for i in range(num_windows):
            block = samples[i * hop:i * hop + self.block_size]
            result[i] = self.detect(block)

        return result

    @property
    def freq_resolution(self) -> float:
        return self.sample_rate / self.block_size


def create_vhf_goertzel(sample_rate: int = 16000) -> GoertzelDetector:
    """Create a Goertzel detector configured for VHF DSC.

    Uses block size of 1 symbol duration for clean per-symbol detection.
    """
    block_size = max(8, int(round(sample_rate / 1200)))

    return GoertzelDetector(
        sample_rate=sample_rate,
        target_freqs=[1300.0, 2100.0],
        block_size=block_size,
    )
