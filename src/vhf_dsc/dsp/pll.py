"""Phase-Locked Loop for symbol synchronization."""

from __future__ import annotations

import numpy as np


class PLL:
    """Digital Phase-Locked Loop for symbol timing recovery.

    Tracks the optimal sampling point for FSK symbol detection.
    """

    def __init__(self, nominal_baud: float, sample_rate: int,
                 loop_bandwidth: float = 0.02, damping: float = 0.707):
        """Initialize PLL.

        Args:
            nominal_baud: Expected baud rate (1200 for VHF DSC)
            sample_rate: Audio sample rate
            loop_bandwidth: Normalized loop bandwidth (0-1)
            damping: Damping factor (0.707 = critically damped)
        """
        self.nominal_baud = nominal_baud
        self.sample_rate = sample_rate
        self.loop_bandwidth = loop_bandwidth
        self.damping = damping

        self._samples_per_symbol = sample_rate / nominal_baud
        self._phase = 0.0
        self._frequency = 0.0
        self._locked = False

        K0 = 4.0 * damping / (1.0 + 2.0 * damping * loop_bandwidth + loop_bandwidth**2)
        K1 = 4.0 * loop_bandwidth**2 / (1.0 + 2.0 * damping * loop_bandwidth + loop_bandwidth**2)
        self._K0 = K0
        self._K1 = K1

    def process(self, error_signal: float) -> tuple[float, bool]:
        """Process one error signal sample and update PLL state.

        Args:
            error_signal: Timing error from the synchronizer

        Returns:
            Tuple of (adjusted_phase, is_locked)
        """
        self._frequency += self._K1 * error_signal
        self._phase += self._samples_per_symbol + self._K0 * error_signal + self._frequency

        if self._phase >= self._samples_per_symbol:
            self._phase -= self._samples_per_symbol
            return self._phase, True

        return self._phase, False

    def reset(self):
        """Reset PLL state."""
        self._phase = 0.0
        self._frequency = 0.0
        self._locked = False

    @property
    def samples_per_symbol(self) -> float:
        return self._samples_per_symbol

    @property
    def is_locked(self) -> bool:
        return self._locked

    @is_locked.setter
    def is_locked(self, value: bool):
        self._locked = value
