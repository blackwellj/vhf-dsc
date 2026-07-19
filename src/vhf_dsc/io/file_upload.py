"""File upload handler for web interface."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import numpy as np

from .wav import read_wav
from .raw import read_real
from ..protocol.constants import INTERNAL_SAMPLE_RATE

ALLOWED_EXTENSIONS = {".wav", ".raw", ".iq", ".bin", ".mp3"}


def _read_mp3(filepath: str) -> tuple[np.ndarray, int]:
    """Decode an MP3 file to float32 samples using pydub.

    Args:
        filepath: Path to MP3 file

    Returns:
        Tuple of (samples_float32, sample_rate)
    """
    from pydub import AudioSegment  # type: ignore[import]

    audio = AudioSegment.from_mp3(filepath)
    # Convert to mono
    audio = audio.set_channels(1)
    sample_rate = audio.frame_rate
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    # Normalize to [-1, 1] based on bit depth
    max_val = float(1 << (audio.sample_width * 8 - 1))
    samples /= max_val
    return samples, sample_rate


class FileUploadHandler:
    """Handle uploaded audio files for decoding."""

    def __init__(self, upload_dir: str = "./uploads",
                 max_size_mb: int = 100):
        self.upload_dir = Path(upload_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, filename: str, data: bytes) -> str:
        """Save uploaded file to upload directory.

        Args:
            filename: Original filename
            data: File contents

        Returns:
            Path to saved file

        Raises:
            ValueError: If file is too large or invalid type
        """
        if len(data) > self.max_size_bytes:
            raise ValueError(f"File too large (max {self.max_size_bytes // (1024*1024)}MB)")

        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")

        save_path = self.upload_dir / filename
        save_path.write_bytes(data)
        return str(save_path)

    def load_audio(self, filepath: str) -> tuple[np.ndarray, int]:
        """Load audio from a saved file.

        Args:
            filepath: Path to audio file

        Returns:
            Tuple of (samples, sample_rate)
        """
        ext = Path(filepath).suffix.lower()

        if ext == ".wav":
            return read_wav(filepath)
        elif ext == ".mp3":
            return _read_mp3(filepath)
        elif ext in (".raw", ".bin"):
            samples = read_real(filepath)
            return samples, INTERNAL_SAMPLE_RATE
        elif ext == ".iq":
            from .raw import read_raw, iq_to_real
            iq = read_raw(filepath)
            return iq_to_real(iq), INTERNAL_SAMPLE_RATE
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def cleanup(self, filepath: str):
        """Remove an uploaded file."""
        path = Path(filepath)
        if path.exists():
            path.unlink()

    def list_uploads(self) -> list[str]:
        """List all uploaded files."""
        return [f.name for f in self.upload_dir.iterdir() if f.is_file()]
