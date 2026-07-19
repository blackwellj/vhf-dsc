"""VHF FSK modulator and demodulator for DSC.

VHF DSC uses:
- Mark frequency: 1300 Hz (bit 1)
- Space frequency: 2100 Hz (bit 0)
- Baud rate: 1200
"""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, lfilter

from ..protocol.constants import VHF_MARK_FREQ, VHF_SPACE_FREQ, VHF_BAUD_RATE, INTERNAL_SAMPLE_RATE
from .filters import apply_dsc_bandpass


class VHFFSKDemodulator:
    """Demodulate VHF DSC FSK signal to bits.

    Uses dual correlator with signal-start-based symbol synchronization.
    The DSC signal structure is: TX delay (silence) -> dot pattern -> phasing -> content.
    We detect the signal start (end of TX delay) and use that as the symbol sync point.
    """

    def __init__(self, sample_rate: int = INTERNAL_SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.baud_rate = VHF_BAUD_RATE
        self.samples_per_symbol = sample_rate / VHF_BAUD_RATE

    def demodulate(self, samples: np.ndarray) -> np.ndarray:
        """Demodulate FSK audio samples to a bit stream."""
        filtered = apply_dsc_bandpass(samples, self.sample_rate)

        energy_diff = self._dual_correlator(filtered)

        bits, symbol_start = self._sync_and_sample(energy_diff)

        return bits

    def demodulate_with_confidence(self, samples: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Demodulate FSK with confidence values."""
        filtered = apply_dsc_bandpass(samples, self.sample_rate)

        energy_diff = self._dual_correlator(filtered)

        bits, confidence, symbol_start = self._sync_and_sample_with_confidence(energy_diff)

        return bits, confidence

    def _dual_correlator(self, samples: np.ndarray) -> np.ndarray:
        """Compute mark vs space energy difference using dual correlators."""
        n = len(samples)
        t = np.arange(n) / self.sample_rate

        mark_sin = np.sin(2 * np.pi * VHF_MARK_FREQ * t)
        mark_cos = np.cos(2 * np.pi * VHF_MARK_FREQ * t)
        space_sin = np.sin(2 * np.pi * VHF_SPACE_FREQ * t)
        space_cos = np.cos(2 * np.pi * VHF_SPACE_FREQ * t)

        mark_i = samples * mark_sin
        mark_q = samples * mark_cos
        space_i = samples * space_sin
        space_q = samples * space_cos

        cutoff = 1200
        b, a = butter(2, cutoff / (self.sample_rate / 2), btype="low")

        mark_i = lfilter(b, a, mark_i)
        mark_q = lfilter(b, a, mark_q)
        space_i = lfilter(b, a, space_i)
        space_q = lfilter(b, a, space_q)

        mark_energy = mark_i ** 2 + mark_q ** 2
        space_energy = space_i ** 2 + space_q ** 2

        return mark_energy - space_energy

    def _find_signal_start(self, energy_diff: np.ndarray, sps: int) -> int:
        """Find where the DSC signal starts (after TX delay silence).

        Uses energy threshold detection: finds first symbol with energy
        above 10% of peak energy.
        """
        num_symbols = len(energy_diff) // sps
        if num_symbols < 5:
            return 0

        energies = np.zeros(num_symbols)
        for i in range(num_symbols):
            start = i * sps
            end = start + sps
            energies[i] = np.mean(np.abs(energy_diff[start:end]))

        peak_energy = np.max(energies)
        if peak_energy < 1e-10:
            return 0

        threshold = peak_energy * 0.1

        for i in range(len(energies)):
            if energies[i] > threshold:
                return i * sps

        return 0

    def _sync_and_sample(self, energy_diff: np.ndarray) -> tuple[np.ndarray, int]:
        """Find signal start and sample at symbol rate."""
        sps = int(round(self.samples_per_symbol))
        if sps < 1:
            sps = 1

        symbol_start = self._find_signal_start(energy_diff, sps)

        num_symbols = (len(energy_diff) - symbol_start) // sps
        bits = np.zeros(num_symbols, dtype=np.int8)

        for i in range(num_symbols):
            start = symbol_start + i * sps
            end = start + sps
            if end > len(energy_diff):
                break

            avg = np.mean(energy_diff[start:end])
            bits[i] = 1 if avg > 0 else 0

        return bits, symbol_start

    def _sync_and_sample_with_confidence(self, energy_diff: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
        """Find signal start and sample with confidence."""
        sps = int(round(self.samples_per_symbol))
        if sps < 1:
            sps = 1

        symbol_start = self._find_signal_start(energy_diff, sps)

        num_symbols = (len(energy_diff) - symbol_start) // sps
        bits = np.zeros(num_symbols, dtype=np.int8)
        confidence = np.zeros(num_symbols)

        for i in range(num_symbols):
            start = symbol_start + i * sps
            end = start + sps
            if end > len(energy_diff):
                break

            avg = np.mean(energy_diff[start:end])
            std = np.std(energy_diff[start:end])

            bits[i] = 1 if avg > 0 else 0

            if std > 1e-10:
                confidence[i] = min(1.0, abs(avg) / (std * 2))
            else:
                confidence[i] = 1.0

        return bits, confidence, symbol_start


class VHFFSKModulator:
    """Modulate bits to VHF DSC FSK audio waveform."""

    def __init__(self, sample_rate: int = INTERNAL_SAMPLE_RATE,
                 baud_rate: int = VHF_BAUD_RATE):
        self.sample_rate = sample_rate
        self.baud_rate = baud_rate
        self.samples_per_bit = sample_rate / baud_rate

    def modulate(self, bits: list[int]) -> np.ndarray:
        """Modulate a bit stream to FSK audio samples with phase continuity."""
        samples_per_bit = int(round(self.samples_per_bit))
        total_samples = len(bits) * samples_per_bit
        audio = np.zeros(total_samples, dtype=np.float32)

        phase = 0.0
        t = np.arange(samples_per_bit) / self.sample_rate

        for i, bit in enumerate(bits):
            freq = VHF_MARK_FREQ if bit == 1 else VHF_SPACE_FREQ

            carrier = np.sin(2 * np.pi * freq * t + phase)
            start = i * samples_per_bit
            end = start + samples_per_bit
            audio[start:end] = carrier

            phase = (2 * np.pi * freq * samples_per_bit / self.sample_rate + phase) % (2 * np.pi)

        return audio

    def modulate_with_shaping(self, bits: list[int]) -> np.ndarray:
        """Modulate with raised-cosine pulse shaping."""
        samples_per_bit = int(round(self.samples_per_bit))
        total_samples = len(bits) * samples_per_bit
        audio = np.zeros(total_samples, dtype=np.float32)

        phase = 0.0
        t = np.arange(samples_per_bit) / self.sample_rate

        for i, bit in enumerate(bits):
            freq = VHF_MARK_FREQ if bit == 1 else VHF_SPACE_FREQ

            carrier = np.sin(2 * np.pi * freq * t + phase)
            window = 0.5 * (1 - np.cos(2 * np.pi * t * self.baud_rate))
            start = i * samples_per_bit
            end = start + samples_per_bit
            audio[start:end] = carrier * window

            phase = (2 * np.pi * freq * samples_per_bit / self.sample_rate + phase) % (2 * np.pi)

        return audio
