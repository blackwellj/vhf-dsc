"""Tests for DSP components."""

import numpy as np
import pytest

from vhf_dsc.dsp.goertzel import GoertzelDetector, create_vhf_goertzel
from vhf_dsc.dsp.vhf_fsk import VHFFSKDemodulator, VHFFSKModulator
from vhf_dsc.protocol.constants import VHF_MARK_FREQ, VHF_SPACE_FREQ, VHF_BAUD_RATE, INTERNAL_SAMPLE_RATE


class TestGoertzel:
    def test_detect_mark(self):
        detector = create_vhf_goertzel(INTERNAL_SAMPLE_RATE)
        t = np.arange(INTERNAL_SAMPLE_RATE) / INTERNAL_SAMPLE_RATE
        signal = np.sin(2 * np.pi * VHF_MARK_FREQ * t)
        magnitudes = detector.detect_stream(signal)
        assert magnitudes[0, 0] > magnitudes[0, 1]

    def test_detect_space(self):
        detector = create_vhf_goertzel(INTERNAL_SAMPLE_RATE)
        t = np.arange(INTERNAL_SAMPLE_RATE) / INTERNAL_SAMPLE_RATE
        signal = np.sin(2 * np.pi * VHF_SPACE_FREQ * t)
        magnitudes = detector.detect_stream(signal)
        assert magnitudes[0, 1] > magnitudes[0, 0]


class TestFSKModDemod:
    def test_modulate_demodulate_roundtrip(self):
        modulator = VHFFSKModulator(INTERNAL_SAMPLE_RATE)
        demodulator = VHFFSKDemodulator(INTERNAL_SAMPLE_RATE)

        bits = [1, 0, 1, 1, 0, 0, 1, 0]
        audio = modulator.modulate(bits)
        decoded = demodulator.demodulate(audio)

        assert len(decoded) > 0

    def test_modulate_output_length(self):
        modulator = VHFFSKModulator(INTERNAL_SAMPLE_RATE)
        bits = [1, 0, 1, 0]
        audio = modulator.modulate(bits)
        samples_per_bit = int(INTERNAL_SAMPLE_RATE / VHF_BAUD_RATE)
        expected_signal = len(bits) * samples_per_bit
        assert len(audio) >= expected_signal
