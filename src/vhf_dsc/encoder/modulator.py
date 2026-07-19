"""DSC modulator - converts DSC messages to FSK audio per ITU-R M.493-16.

Supports realistic radio channel simulation for test signal generation.
"""

from __future__ import annotations

import numpy as np

from ..protocol.message import DSCMessage
from ..protocol.constants import (
    VHF_BAUD_RATE, INTERNAL_SAMPLE_RATE,
    TX_DELAY_MS, TX_TRAILER_MS, DOT_PATTERN_BITS_VHF,
)
from ..protocol.characters import encode_char, code_to_bits
from ..protocol.symbols import SYM_PHASING_DX, SYM_PHASING_RX
from .serializer import DSCSerializer
from .channel_simulator import RadioChannelSimulator
from ..dsp.vhf_fsk import VHFFSKModulator


class DSCModulator:
    """Modulate DSC messages to audio waveforms per ITU-R M.493-16."""

    def __init__(self, sample_rate: int = INTERNAL_SAMPLE_RATE,
                 baud_rate: int = VHF_BAUD_RATE):
        self.sample_rate = sample_rate
        self.baud_rate = baud_rate
        self._serializer = DSCSerializer()
        self._fsk = VHFFSKModulator(sample_rate, baud_rate)
        self._channel = RadioChannelSimulator(sample_rate)

    def _symbols_to_bits(self, symbols: list[int]) -> list[int]:
        """Convert symbol numbers to raw bits."""
        bits = []
        for sym in symbols:
            code = encode_char(sym)
            bits.extend(code_to_bits(code))
        return bits

    def _build_full_bitstream(self, msg: DSCMessage) -> list[int]:
        """Build complete bit stream: dot pattern + phasing + call content.

        Phasing per ITU-R M.493-16 Section 3.2:
        6 DX symbols (125) and 8 RX symbols (111-104), transmitted alternately:
        125, 111, 125, 110, 125, 109, 125, 108, 125, 107, 125, 106, 105, 104
        """
        bits = []

        for i in range(DOT_PATTERN_BITS_VHF):
            bits.append(i % 2)

        rx_symbols = list(SYM_PHASING_RX)
        for i in range(6):
            bits.extend(code_to_bits(encode_char(SYM_PHASING_DX)))
            if rx_symbols:
                bits.extend(code_to_bits(encode_char(rx_symbols.pop(0))))

        while rx_symbols:
            bits.extend(code_to_bits(encode_char(rx_symbols.pop(0))))

        symbols = self._serializer.serialize(msg)
        bits.extend(self._symbols_to_bits(symbols))

        return bits

    def modulate(self, msg: DSCMessage,
                 pulse_shaping: bool = False,
                 channel_model: str = "perfect",
                 snr_db: float | None = None,
                 seed: int | None = None) -> np.ndarray:
        """Modulate a DSCMessage to audio samples.

        Args:
            msg: DSCMessage to modulate
            pulse_shaping: Apply raised-cosine pulse shaping
            channel_model: Channel impairment model:
                - "perfect": Clean signal
                - "good": Strong signal, minimal noise
                - "moderate": Typical conditions
                - "poor": Weak signal, fading
                - "marginal": Near decode threshold
                - "custom": Use snr_db parameter
            snr_db: SNR for custom model
            seed: Random seed for reproducibility

        Returns:
            Audio samples (possibly with channel impairments)
        """
        bits = self._build_full_bitstream(msg)

        delay_samples = int(self.sample_rate * TX_DELAY_MS / 1000)
        trailer_samples = int(self.sample_rate * TX_TRAILER_MS / 1000)

        delay_audio = np.zeros(delay_samples, dtype=np.float32)
        trailer_audio = np.zeros(trailer_samples, dtype=np.float32)

        if pulse_shaping:
            signal_audio = self._fsk.modulate_with_shaping(bits)
        else:
            signal_audio = self._fsk.modulate(bits)

        audio = np.concatenate([delay_audio, signal_audio, trailer_audio])

        if channel_model != "perfect":
            audio = self._channel.apply_channel_model(
                audio, model=channel_model, snr_db=snr_db, seed=seed)

        return audio

    def modulate_bits(self, bits: list[int],
                      pulse_shaping: bool = False,
                      channel_model: str = "perfect",
                      snr_db: float | None = None,
                      seed: int | None = None) -> np.ndarray:
        """Modulate a raw bit stream to audio."""
        delay_samples = int(self.sample_rate * TX_DELAY_MS / 1000)
        trailer_samples = int(self.sample_rate * TX_TRAILER_MS / 1000)

        delay_audio = np.zeros(delay_samples, dtype=np.float32)
        trailer_audio = np.zeros(trailer_samples, dtype=np.float32)

        if pulse_shaping:
            signal_audio = self._fsk.modulate_with_shaping(bits)
        else:
            signal_audio = self._fsk.modulate(bits)

        audio = np.concatenate([delay_audio, signal_audio, trailer_audio])

        if channel_model != "perfect":
            audio = self._channel.apply_channel_model(
                audio, model=channel_model, snr_db=snr_db, seed=seed)

        return audio

    def modulate_messages(self, messages: list[DSCMessage],
                          gap_ms: int = 500,
                          channel_model: str = "perfect",
                          snr_db: float | None = None,
                          seed: int | None = None) -> np.ndarray:
        """Modulate multiple messages with gaps."""
        gap_samples = int(self.sample_rate * gap_ms / 1000)
        gap_audio = np.zeros(gap_samples, dtype=np.float32)

        parts = []
        for i, msg in enumerate(messages):
            if i > 0:
                parts.append(gap_audio)
            parts.append(self.modulate(
                msg, channel_model=channel_model,
                snr_db=snr_db, seed=seed))

        return np.concatenate(parts)

    def generate_test_suite(self, msg: DSCMessage,
                            seed: int = 42) -> dict[str, np.ndarray]:
        """Generate a complete test suite with all channel models.

        Returns:
            Dictionary of {model_name: audio_samples}
        """
        clean = self.modulate(msg, channel_model="perfect")
        return self._channel.generate_test_suite(clean, seed=seed)
