"""Raw IQ sample file read/write."""

from __future__ import annotations

import numpy as np

from ..protocol.constants import INTERNAL_SAMPLE_RATE


def read_raw(filepath: str, sample_rate: int = INTERNAL_SAMPLE_RATE) -> np.ndarray:
    """Read raw complex IQ samples from a file.

    Args:
        filepath: Path to raw IQ file
        sample_rate: Sample rate (for metadata, not stored in file)

    Returns:
        Complex numpy array of IQ samples
    """
    data = np.fromfile(filepath, dtype=np.complex64)
    return data


def write_raw(filepath: str, samples: np.ndarray):
    """Write complex IQ samples to a file.

    Args:
        filepath: Output path
        samples: Complex numpy array of IQ samples
    """
    samples.astype(np.complex64).tofile(filepath)


def read_real(filepath: str) -> np.ndarray:
    """Read raw real-valued (float32) samples from a file.

    Args:
        filepath: Path to raw samples file

    Returns:
        Float32 numpy array
    """
    return np.fromfile(filepath, dtype=np.float32)


def write_real(filepath: str, samples: np.ndarray):
    """Write real-valued (float32) samples to a file.

    Args:
        filepath: Output path
        samples: Float32 numpy array
    """
    samples.astype(np.float32).tofile(filepath)


def iq_to_real(iq_samples: np.ndarray) -> np.ndarray:
    """Convert complex IQ samples to real audio samples.

    Extracts the magnitude envelope or real component.

    Args:
        iq_samples: Complex IQ samples

    Returns:
        Real-valued audio samples
    """
    return np.real(iq_samples)


def real_to_iq(real_samples: np.ndarray) -> np.ndarray:
    """Convert real audio samples to complex IQ (analytic signal).

    Uses Hilbert transform to create analytic signal.

    Args:
        real_samples: Real audio samples

    Returns:
        Complex IQ samples
    """
    from scipy.signal import hilbert
    return hilbert(real_samples)
