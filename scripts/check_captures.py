"""Check UDP capture status and list saved files."""
import os
from datetime import datetime

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "udp_captures")

print("UDP Capture Status")
print("=" * 50)

if not os.path.exists(SAVE_DIR):
    print(f"Capture directory does not exist: {SAVE_DIR}")
    print("Monitor may not be running.")
    exit(1)

files = [f for f in os.listdir(SAVE_DIR) if f.endswith('.wav')]

if not files:
    print(f"No captures yet in: {SAVE_DIR}")
    print("Waiting for rtl-airband transmissions...")
else:
    print(f"Capture directory: {SAVE_DIR}")
    print(f"Total captures: {len(files)}")
    print()
    
    total_size = 0
    for f in sorted(files):
        filepath = os.path.join(SAVE_DIR, f)
        stat = os.stat(filepath)
        total_size += stat.st_size
        duration = stat.st_size / (16000 * 2)  # Approximate
        print(f"  {f}")
        print(f"    Size: {stat.st_size / 1024:.1f} KB, Duration: ~{duration:.1f}s")
    
    print(f"\nTotal: {total_size / 1024:.1f} KB")
