"""Digital filters for DSC signal processing."""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, lfilter, firwin


def bandpass_filter(samples: np.ndarray, low_freq: float, high_freq: float,
                    sample_rate: int, order: int = 4) -> np.ndarray:
    """Apply a Butterworth bandpass filter.

    Args:
        samples: Input audio samples
        low_freq: Lower cutoff frequency (Hz)
        high_freq: Upper cutoff frequency (Hz)
        sample_rate: Sample rate (Hz)
        order: Filter order

    Returns:
        Filtered samples
    """
    nyquist = sample_rate / 2.0
    low = low_freq / nyquist
    high = high_freq / nyquist
    b, a = butter(order, [low, high], btype="band")
    return lfilter(b, a, samples)


def lowpass_filter(samples: np.ndarray, cutoff_freq: float,
                   sample_rate: int, order: int = 4) -> np.ndarray:
    """Apply a Butterworth lowpass filter.

    Args:
        samples: Input audio samples
        cutoff_freq: Cutoff frequency (Hz)
        sample_rate: Sample rate (Hz)
        order: Filter order

    Returns:
        Filtered samples
    """
    nyquist = sample_rate / 2.0
    cutoff = cutoff_freq / nyquist
    b, a = butter(order, cutoff, btype="low")
    return lfilter(b, a, samples)


def matched_filter(samples: np.ndarray, symbol_duration: float,
                   sample_rate: int) -> np.ndarray:
    """Apply a matched filter optimized for the symbol duration.

    For DSC at 1200 baud, symbol duration is 1/1200 = 833.33 us.

    Args:
        samples: Input audio samples
        symbol_duration: Duration of one symbol in seconds
        sample_rate: Sample rate (Hz)

    Returns:
        Filtered samples
    """
    num_taps = int(symbol_duration * sample_rate)
    if num_taps < 1:
        num_taps = 1

    taps = np.ones(num_taps) / num_taps
    return np.convolve(samples, taps, mode="same")


def create_dsc_bandpass(sample_rate: int = 16000) -> np.ndarray:
    """Create filter coefficients for DSC VHF bandpass (1000-2400 Hz).

    Returns:
        Tuple of (b, a) filter coefficients
    """
    nyquist = sample_rate / 2.0
    low = 1000.0 / nyquist
    high = 2400.0 / nyquist
    return butter(4, [low, high], btype="band")


def apply_dsc_bandpass(samples: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
    """Apply DSC-specific bandpass filter (1000-2400 Hz).

    Args:
        samples: Input audio samples
        sample_rate: Sample rate (Hz)

    Returns:
        Filtered samples
    """
    b, a = create_dsc_bandpass(sample_rate)
    return lfilter(b, a, samples)
