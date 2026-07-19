"""Tests for I/O components."""

import os
import tempfile
import numpy as np
import pytest

from vhf_dsc.io.wav import read_wav, write_wav, write_wav_normalized
from vhf_dsc.io.raw import read_real, write_real
from vhf_dsc.protocol.constants import INTERNAL_SAMPLE_RATE


class TestWAV:
    def test_write_read_roundtrip(self):
        samples = np.random.randn(16000).astype(np.float32)
        filepath = os.path.join(tempfile.gettempdir(), "test_dsc.wav")
        try:
            write_wav(filepath, samples, INTERNAL_SAMPLE_RATE)
            read_samples, sr = read_wav(filepath)
            assert sr == INTERNAL_SAMPLE_RATE
            assert len(read_samples) == len(samples)
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_write_normalized(self):
        samples = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        filepath = os.path.join(tempfile.gettempdir(), "test_dsc_norm.wav")
        try:
            write_wav_normalized(filepath, samples, INTERNAL_SAMPLE_RATE)
            read_samples, _ = read_wav(filepath)
            peak = np.max(np.abs(read_samples))
            assert abs(peak - 0.9) < 0.01
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)


class TestRaw:
    def test_write_read_roundtrip(self):
        samples = np.random.randn(16000).astype(np.float32)
        filepath = os.path.join(tempfile.gettempdir(), "test_dsc.raw")
        try:
            write_real(filepath, samples)
            read_samples = read_real(filepath)
            np.testing.assert_array_almost_equal(read_samples, samples)
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
