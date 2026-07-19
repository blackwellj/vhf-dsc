"""Replay audio files as UDP stream for testing."""

import sys
import argparse
sys.path.insert(0, ".")

from vhf_dsc.io.wav import read_wav
from vhf_dsc.io.udp_stream import UDPStreamSender
from vhf_dsc.protocol.constants import INTERNAL_SAMPLE_RATE


def main():
    parser = argparse.ArgumentParser(description="Replay audio as UDP stream")
    parser.add_argument("file", help="Audio file to replay")
    parser.add_argument("--host", default="127.0.0.1", help="Target host")
    parser.add_argument("--port", type=int, default=6000, help="Target port")
    parser.add_argument("--realtime", action="store_true", help="Real-time pacing")
    parser.add_argument("--loop", action="store_true", help="Loop playback")
    args = parser.parse_args()

    samples, sr = read_wav(args.file)
    sender = UDPStreamSender(args.host, args.port, sr)

    print(f"Replaying {args.file} to {args.host}:{args.port}")
    print(f"Duration: {len(samples) / sr:.2f}s")

    try:
        while True:
            if args.realtime:
                sender.send_file(samples)
            else:
                sender.send(samples)
            if not args.loop:
                break
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        sender.close()


if __name__ == "__main__":
    main()
