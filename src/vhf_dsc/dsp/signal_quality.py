"""Signal quality estimation for DSC reception."""

from __future__ import annotations

import numpy as np

from ..protocol.constants import GOERTZEL_THRESHOLD


class SignalQualityEstimator:
    """Estimate signal quality metrics for DSC reception."""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self._snr_history: list[float] = []
        self._level_history: list[float] = []

    def estimate_snr(self, mark_magnitude: float,
                     space_magnitude: float) -> float:
        """Estimate SNR from Goertzel magnitudes.

        Args:
            mark_magnitude: Magnitude at 1300 Hz
            space_magnitude: Magnitude at 2100 Hz

        Returns:
            Estimated SNR in dB
        """
        signal = max(mark_magnitude, space_magnitude)
        noise = min(mark_magnitude, space_magnitude)

        if noise < 1e-10:
            noise = 1e-10

        snr = 20 * np.log10(signal / noise)
        self._snr_history.append(snr)
        if len(self._snr_history) > self.window_size:
            self._snr_history.pop(0)

        return snr

    def estimate_level(self, samples: np.ndarray) -> float:
        """Estimate signal level (RMS).

        Args:
            samples: Audio samples

        Returns:
            RMS level
        """
        level = np.sqrt(np.mean(samples ** 2))
        self._level_history.append(level)
        if len(self._level_history) > self.window_size:
            self._level_history.pop(0)

        return level

    def get_average_snr(self) -> float:
        """Get average SNR over the history window."""
        if not self._snr_history:
            return 0.0
        return float(np.mean(self._snr_history))

    def get_average_level(self) -> float:
        """Get average signal level over the history window."""
        if not self._level_history:
            return 0.0
        return float(np.mean(self._level_history))

    def is_signal_present(self, mark_magnitude: float,
                          space_magnitude: float,
                          threshold: float = GOERTZEL_THRESHOLD) -> bool:
        """Check if a valid DSC signal is present.

        Args:
            mark_magnitude: Magnitude at 1300 Hz
            space_magnitude: Magnitude at 2100 Hz
            threshold: Minimum magnitude threshold

        Returns:
            True if DSC signal is detected
        """
        signal = max(mark_magnitude, space_magnitude)
        return signal > threshold

    def get_quality_score(self) -> float:
        """Get overall quality score (0-1).

        Combines SNR and level into a single quality metric.
        """
        avg_snr = self.get_average_snr()
        avg_level = self.get_average_level()

        snr_score = min(1.0, max(0.0, avg_snr / 20.0))
        level_score = min(1.0, max(0.0, avg_level * 10.0))

        return 0.7 * snr_score + 0.3 * level_score

    def reset(self):
        """Reset history."""
        self._snr_history.clear()
        self._level_history.clear()
