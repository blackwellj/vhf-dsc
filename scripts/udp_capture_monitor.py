"""Monitor UDP port 5555 for rtl-airband audio and save captures for DSC decoding.

Uses SO_REUSEADDR to share port with existing ncat listener.
"""

import socket
import time
import os
import signal
import sys
import wave
import numpy as np
from datetime import datetime

UDP_PORT = 5555
UDP_HOST = "0.0.0.0"
SAMPLE_RATE = 16000

# Capture settings
MIN_CAPTURE_SECONDS = 2
SILENCE_TIMEOUT = 5
MAX_CAPTURE_SECONDS = 300

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "udp_captures")


class UDPCaptureMonitor:
    def __init__(self, port=UDP_PORT, save_dir=SAVE_DIR):
        self.port = port
        self.save_dir = save_dir
        self._sock = None
        self._running = False
        self._capturing = False
        self._capture_buffer = bytearray()
        self._capture_start = None
        self._last_activity = None
        self._capture_count = 0

        os.makedirs(self.save_dir, exist_ok=True)
        print(f"Capture directory: {self.save_dir}")

    def start(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((UDP_HOST, self.port))
        self._running = True
        self._sock.settimeout(1.0)

        print(f"Monitoring UDP {UDP_HOST}:{self.port}")
        print(f"Saving captures to: {self.save_dir}")
        print(f"Press Ctrl+C to stop")
        print(f"Waiting for rtl-airband transmissions...\n")

        while self._running:
            try:
                data, addr = self._sock.recvfrom(65536)
                self._handle_data(data, addr)
            except socket.timeout:
                if self._capturing:
                    elapsed = time.time() - self._capture_start
                    if elapsed >= MIN_CAPTURE_SECONDS and (time.time() - self._last_activity) >= SILENCE_TIMEOUT:
                        self._save_capture()
                    elif elapsed >= MAX_CAPTURE_SECONDS:
                        self._save_capture()
            except socket.error as e:
                if self._running:
                    print(f"Socket error: {e}")

    def _handle_data(self, data, addr):
        now = time.time()
        self._capture_buffer.extend(data)

        if not self._capturing:
            self._capturing = True
            self._capture_start = now
            self._last_activity = now
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Capture started from {addr[0]}:{addr[1]}")
        else:
            self._last_activity = now

    def _save_capture(self):
        if len(self._capture_buffer) < SAMPLE_RATE * 2:
            self._capture_buffer.clear()
            self._capturing = False
            return

        samples = np.frombuffer(self._capture_buffer, dtype=np.int16)
        samples_float = samples.astype(np.float32) / 32768.0
        rms = np.sqrt(np.mean(samples_float ** 2))

        duration = len(samples) / SAMPLE_RATE
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dsc_capture_{timestamp}_{int(rms*10000):04d}rms.wav"
        filepath = os.path.join(self.save_dir, filename)

        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(self._capture_buffer)

        self._capture_count += 1
        print(f"  Saved: {filename} ({duration:.1f}s, RMS={rms:.4f})")

        self._capture_buffer.clear()
        self._capturing = False
        self._capture_start = None
        self._last_activity = None

    def stop(self):
        self._running = False
        if self._capturing:
            self._save_capture()
        if self._sock:
            self._sock.close()
        print(f"\nStopped. Saved {self._capture_count} capture(s) to {self.save_dir}")


def main():
    monitor = UDPCaptureMonitor()

    def signal_handler(sig, frame):
        monitor.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        monitor.start()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
