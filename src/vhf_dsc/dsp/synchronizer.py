"""Symbol synchronizer for FSK demodulation."""

from __future__ import annotations

import numpy as np

from .pll import PLL
from ..protocol.constants import VHF_BAUD_RATE


class SymbolSynchronizer:
    """Symbol-level synchronizer for FSK bitstream.

    Combines PLL tracking with early-late gate synchronizer
    to find optimal symbol sampling points.
    """

    def __init__(self, sample_rate: int, baud_rate: int = VHF_BAUD_RATE):
        self.sample_rate = sample_rate
        self.baud_rate = baud_rate
        self.pll = PLL(baud_rate, sample_rate)

        self._buffer = np.zeros(int(sample_rate / baud_rate) * 3)
        self._buf_idx = 0
        self._symbol_count = 0
        self._lock_threshold = 10
        self._lock_count = 0

    def feed(self, samples: np.ndarray) -> list[int]:
        """Feed audio samples and extract synchronized symbols.

        Args:
            samples: Audio samples

        Returns:
            List of detected symbol values (0 or 1)
        """
        symbols = []

        for sample in samples:
            self._buffer[self._buf_idx] = sample
            self._buf_idx += 1

            phase, ready = self.pll.process(0.0)

            if ready:
                sym_idx = int(self.pll.samples_per_symbol)
                if self._buf_idx >= sym_idx:
                    symbol = 1 if self._buffer[sym_idx - 1] > 0 else 0
                    symbols.append(symbol)
                    self._symbol_count += 1
                    self._buf_idx = 0

                    if self._symbol_count >= self._lock_threshold:
                        self.pll.is_locked = True

        return symbols

    def feed_with_early_late(self, samples: np.ndarray) -> list[int]:
        """Feed samples using early-late gate synchronization.

        More robust than basic PLL for noisy signals.

        Args:
            samples: Audio samples

        Returns:
            List of detected symbol values
        """
        symbols = []
        sps = int(self.pll.samples_per_symbol)

        i = 0
        while i < len(samples) - sps:
            early = samples[i + sps // 4]
            on_time = samples[i + sps // 2]
            late = samples[i + 3 * sps // 4]

            error = (late - early) * on_time
            phase, _ = self.pll.process(error)

            symbol = 1 if on_time > 0 else 0
            symbols.append(symbol)
            self._symbol_count += 1

            if self._symbol_count >= self._lock_threshold:
                self.pll.is_locked = True

            i += sps

        return symbols

    def reset(self):
        """Reset synchronizer state."""
        self.pll.reset()
        self._buf_idx = 0
        self._symbol_count = 0
        self._lock_count = 0

    @property
    def is_locked(self) -> bool:
        return self.pll.is_locked
