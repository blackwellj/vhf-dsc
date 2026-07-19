"""UDP audio stream receiver and sender for RTL-Airband integration."""

from __future__ import annotations

import asyncio
import socket
import struct
from typing import Callable, Optional

import numpy as np

from ..protocol.constants import INTERNAL_SAMPLE_RATE


class UDPStreamReceiver:
    """Receive PCM16 mono audio over UDP from RTL-Airband.

    Designed for Pi nodes sending 16000 Hz, 16-bit PCM mono audio.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 6000,
                 sample_rate: int = INTERNAL_SAMPLE_RATE):
        self.host = host
        self.port = port
        self.sample_rate = sample_rate
        self._sock: Optional[socket.socket] = None
        self._running = False
        self._on_audio: Optional[Callable[[np.ndarray], None]] = None
        self._buffer = bytearray()
        self._chunk_samples = sample_rate // 10

    def start(self):
        """Start the UDP receiver (blocking)."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind((self.host, self.port))
        self._running = True

        while self._running:
            data, addr = self._sock.recvfrom(65536)
            self._buffer.extend(data)
            self._process_buffer()

    async def start_async(self):
        """Start the UDP receiver (async)."""
        loop = asyncio.get_event_loop()
        loop.sock_setblocking(self._sock, False)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setblocking(False)
        self._sock.bind((self.host, self.port))
        self._running = True

        while self._running:
            try:
                data, addr = await loop.sock_recvfrom(self._sock, 65536)
                self._buffer.extend(data)
                self._process_buffer()
            except BlockingIOError:
                await asyncio.sleep(0.01)

    def _process_buffer(self):
        """Process accumulated buffer into audio chunks."""
        bytes_per_sample = 2
        chunk_bytes = self._chunk_samples * bytes_per_sample

        while len(self._buffer) >= chunk_bytes:
            chunk = self._buffer[:chunk_bytes]
            self._buffer = self._buffer[chunk_bytes:]

            samples = np.frombuffer(chunk, dtype=np.int16)
            samples = samples.astype(np.float32) / 32768.0

            if self._on_audio:
                self._on_audio(samples)

    def stop(self):
        """Stop the UDP receiver."""
        self._running = False
        if self._sock:
            self._sock.close()

    def on_audio(self, callback: Callable[[np.ndarray], None]):
        """Register audio callback."""
        self._on_audio = callback

    @property
    def is_running(self) -> bool:
        return self._running


class UDPStreamSender:
    """Send PCM16 mono audio over UDP (for replay)."""

    def __init__(self, host: str = "127.0.0.1", port: int = 6000,
                 sample_rate: int = INTERNAL_SAMPLE_RATE,
                 chunk_ms: int = 100):
        self.host = host
        self.port = port
        self.sample_rate = sample_rate
        self.chunk_ms = chunk_ms
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._chunk_samples = int(sample_rate * chunk_ms / 1000)

    def send(self, samples: np.ndarray):
        """Send audio samples over UDP.

        Args:
            samples: Audio samples (float32, -1.0 to 1.0)
        """
        pcm16 = (samples * 32767).astype(np.int16).tobytes()

        for i in range(0, len(pcm16), self._chunk_samples * 2):
            chunk = pcm16[i:i + self._chunk_samples * 2]
            self._sock.sendto(chunk, (self.host, self.port))

    def send_file(self, samples: np.ndarray):
        """Send samples with real-time pacing."""
        import time

        chunk_bytes = self._chunk_samples * 2
        chunk_interval = self.chunk_ms / 1000.0

        pcm16 = (samples * 32767).astype(np.int16)

        for i in range(0, len(pcm16), self._chunk_samples):
            chunk = pcm16[i:i + self._chunk_samples]
            self._sock.sendto(chunk.tobytes(), (self.host, self.port))
            time.sleep(chunk_interval)

    def close(self):
        """Close the UDP socket."""
        self._sock.close()
