"""Tests for UDP monitor PCM input conversion."""

import numpy as np

from cli.monitor_server import DSCMonitor, decode_pcm_chunk


def test_decode_float32_pcm_preserves_samples():
    expected = np.array([-1.0, -0.25, 0.0, 0.5, 1.0], dtype="<f4")

    decoded = decode_pcm_chunk(expected.tobytes(), "f32le")

    assert decoded.dtype == np.float32
    np.testing.assert_array_equal(decoded, expected.astype(np.float32))


def test_decode_int16_pcm_normalizes_samples():
    encoded = np.array([-32768, -16384, 0, 16384, 32767], dtype="<i2")

    decoded = decode_pcm_chunk(encoded.tobytes(), "s16le")

    assert decoded.dtype == np.float32
    np.testing.assert_allclose(
        decoded,
        np.array([-1.0, -0.5, 0.0, 0.5, 32767 / 32768], dtype=np.float32),
    )


def test_monitor_processes_configured_float32_udp_payload(tmp_path):
    expected = np.array([-0.75, 0.25, 0.5, -0.125], dtype="<f4")
    payload = expected.tobytes()
    processed = []

    class RecordingDecoder:
        def process(self, samples):
            processed.append(samples.copy())
            return []

    monitor = DSCMonitor(
        save_dir=str(tmp_path),
        chunk_size=len(payload),
        input_format="f32le",
    )
    monitor.decoder = RecordingDecoder()

    monitor._process_data(payload, ("127.0.0.1", 12345))

    assert len(processed) == 1
    np.testing.assert_array_equal(processed[0], expected.astype(np.float32))
