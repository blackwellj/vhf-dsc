"""Quick test: Monitor UDP 5555 and save first capture."""
import socket
import os
import wave
import time
from datetime import datetime

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "udp_captures")
os.makedirs(SAVE_DIR, exist_ok=True)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('0.0.0.0', 5555))
sock.settimeout(60)  # 60 second timeout

print(f"Listening on UDP 5555... (timeout: 60s)")
print(f"Save dir: {SAVE_DIR}")

buffer = bytearray()
start_time = None

try:
    while True:
        try:
            data, addr = sock.recvfrom(65536)
            buffer.extend(data)
            
            if start_time is None:
                start_time = time.time()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] First packet from {addr}")
            
            elapsed = time.time() - start_time
            print(f"  Received {len(data)} bytes (total: {len(buffer)}, {elapsed:.1f}s)")
            
        except socket.timeout:
            if len(buffer) > 0:
                print("\nTimeout - saving capture...")
                break
            else:
                print("No data received, exiting.")
                break
finally:
    sock.close()

if len(buffer) > 32000:  # At least 1 second
    duration = len(buffer) / (16000 * 2)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"dsc_test_{timestamp}.wav"
    filepath = os.path.join(SAVE_DIR, filename)
    
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(buffer)
    
    print(f"\nSaved: {filename} ({duration:.1f}s)")
else:
    print(f"\nNot enough data to save ({len(buffer)} bytes)")
