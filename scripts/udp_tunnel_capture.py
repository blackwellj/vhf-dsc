"""Background UDP capture via Bitvise SSH tunnel."""
import socket
import os
import wave
import time
import signal
import sys
from datetime import datetime

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "udp_captures")
os.makedirs(SAVE_DIR, exist_ok=True)

TUNNEL_HOST = "127.0.0.1"
TUNNEL_PORT = 5555
SAMPLE_RATE = 16000
CHUNK_SIZE = 320  # 100ms at 16kHz, 16-bit mono

# Capture settings
MIN_CAPTURE_SECONDS = 2
SILENCE_TIMEOUT = 3  # Seconds without data to end capture
MAX_CAPTURE_SECONDS = 300

_running = True
_capturing = False
_capture_buffer = bytearray()
_capture_start = None
_last_activity = None
_capture_count = 0


def signal_handler(sig, frame):
    global _running
    _running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def save_capture():
    global _capture_buffer, _capturing, _capture_start, _last_activity, _capture_count
    
    if len(_capture_buffer) < SAMPLE_RATE * 2:
        _capture_buffer.clear()
        _capturing = False
        return
    
    duration = len(_capture_buffer) / (SAMPLE_RATE * 2)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Calculate RMS for filename
    import numpy as np
    samples = np.frombuffer(_capture_buffer, dtype=np.int16)
    rms = np.sqrt(np.mean((samples.astype(np.float32) / 32768.0) ** 2))
    
    filename = f"dsc_capture_{ts}_{int(rms*10000):04d}rms.wav"
    filepath = os.path.join(SAVE_DIR, filename)
    
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(_capture_buffer)
    
    _capture_count += 1
    print(f"  Saved: {filename} ({duration:.1f}s, RMS={rms:.4f})")
    
    _capture_buffer.clear()
    _capturing = False
    _capture_start = None
    _last_activity = None


def main():
    global _capturing, _capture_start, _last_activity
    
    print(f"Monitoring tunnel {TUNNEL_HOST}:{TUNNEL_PORT}")
    print(f"Saving to: {SAVE_DIR}")
    print(f"Press Ctrl+C to stop\n")
    
    while _running:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((TUNNEL_HOST, TUNNEL_PORT))
            
            while _running:
                try:
                    data = sock.recv(65536)
                    if not data:
                        break
                    
                    now = time.time()
                    _capture_buffer.extend(data)
                    
                    if not _capturing:
                        _capturing = True
                        _capture_start = now
                        _last_activity = now
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Capture started")
                    else:
                        _last_activity = now
                    
                    # Check if capture should end
                    if _capturing:
                        elapsed = now - _capture_start
                        silence = now - (_last_activity or now)
                        
                        if silence >= SILENCE_TIMEOUT and elapsed >= MIN_CAPTURE_SECONDS:
                            save_capture()
                        elif elapsed >= MAX_CAPTURE_SECONDS:
                            save_capture()
                
                except socket.timeout:
                    # Check if we should end capture due to silence
                    if _capturing:
                        now = time.time()
                        silence = now - (_last_activity or now)
                        elapsed = now - _capture_start
                        
                        if silence >= SILENCE_TIMEOUT and elapsed >= MIN_CAPTURE_SECONDS:
                            save_capture()
            
            sock.close()
        
        except (socket.timeout, ConnectionRefusedError, OSError):
            time.sleep(0.5)
    
    # Save any remaining data
    if _capturing:
        save_capture()
    
    print(f"\nStopped. Saved {_capture_count} capture(s)")


if __name__ == "__main__":
    main()
