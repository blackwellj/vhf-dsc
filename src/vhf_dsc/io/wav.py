"""WAV file read/write for DSC audio."""

from __future__ import annotations

import numpy as np
import soundfile as sf

from ..protocol.constants import INTERNAL_SAMPLE_RATE


def read_wav(filepath: str) -> tuple[np.ndarray, int]:
    """Read a WAV file and return samples and sample rate.

    Args:
        filepath: Path to WAV file

    Returns:
        Tuple of (samples_array, sample_rate)
    """
    data, sample_rate = sf.read(filepath, dtype="float32")

    if data.ndim > 1:
        data = np.mean(data, axis=1)

    return data, sample_rate


def write_wav(filepath: str, samples: np.ndarray,
              sample_rate: int = INTERNAL_SAMPLE_RATE):
    """Write audio samples to a WAV file.

    Args:
        filepath: Output path
        samples: Audio samples (float32, -1.0 to 1.0)
        sample_rate: Sample rate in Hz
    """
    sf.write(filepath, samples, sample_rate, subtype="PCM_16")


def write_wav_normalized(filepath: str, samples: np.ndarray,
                         sample_rate: int = INTERNAL_SAMPLE_RATE):
    """Write WAV with automatic normalization to 90% peak.

    Args:
        filepath: Output path
        samples: Audio samples
        sample_rate: Sample rate in Hz
    """
    peak = np.max(np.abs(samples))
    if peak > 0:
        samples = samples * 0.9 / peak
    write_wav(filepath, samples, sample_rate)
