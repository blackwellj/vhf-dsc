"""Tests for Goertzel detector."""

import numpy as np

from vhf_dsc.dsp.goertzel import GoertzelDetector, create_vhf_goertzel
from vhf_dsc.protocol.constants import VHF_MARK_FREQ, VHF_SPACE_FREQ, INTERNAL_SAMPLE_RATE


class TestGoertzelDetector:
    def test_mark_detection(self):
        detector = create_vhf_goertzel(INTERNAL_SAMPLE_RATE)
        t = np.arange(INTERNAL_SAMPLE_RATE) / INTERNAL_SAMPLE_RATE
        signal = np.sin(2 * np.pi * VHF_MARK_FREQ * t)
        magnitudes = detector.detect_stream(signal)
        assert magnitudes.shape[1] == 2
        assert magnitudes[0, 0] > magnitudes[0, 1]

    def test_space_detection(self):
        detector = create_vhf_goertzel(INTERNAL_SAMPLE_RATE)
        t = np.arange(INTERNAL_SAMPLE_RATE) / INTERNAL_SAMPLE_RATE
        signal = np.sin(2 * np.pi * VHF_SPACE_FREQ * t)
        magnitudes = detector.detect_stream(signal)
        assert magnitudes[0, 1] > magnitudes[0, 0]

    def test_noise(self):
        detector = create_vhf_goertzel(INTERNAL_SAMPLE_RATE)
        noise = np.random.randn(INTERNAL_SAMPLE_RATE) * 0.1
        magnitudes = detector.detect_stream(noise)
        assert magnitudes[0, 0] < magnitudes[0, 0] + magnitudes[0, 1]

    def test_freq_resolution(self):
        detector = create_vhf_goertzel(INTERNAL_SAMPLE_RATE)
        assert detector.freq_resolution > 0
