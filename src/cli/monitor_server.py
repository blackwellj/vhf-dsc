"""DSC UDP Monitor - Listens on UDP port and decodes DSC messages."""

import argparse
import asyncio
import json
import logging
import os
import signal
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from vhf_dsc.decoder import DSCDecoderPipeline
from vhf_dsc.protocol.constants import INTERNAL_SAMPLE_RATE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class DSCMonitor:
    """Monitors UDP port for DSC audio and decodes messages."""

    def __init__(self, port: int = 6000, sample_rate: int = INTERNAL_SAMPLE_RATE,
                 save_dir: str = "./dsc_messages", chunk_size: int = 48000):
        self.port = port
        self.sample_rate = sample_rate
        self.save_dir = Path(save_dir)
        self.chunk_size = chunk_size
        self.save_dir.mkdir(parents=True, exist_ok=True)

        self.decoder = DSCDecoderPipeline(sample_rate)
        self.sock = None
        self.running = False
        self.message_count = 0
        self.audio_buffer = bytearray()

    def start(self):
        """Start the UDP monitor (blocking)."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', self.port))
        self.running = True

        logger.info(f"Listening on UDP port {self.port}")
        logger.info(f"Saving decoded messages to {self.save_dir}")

        def signal_handler(sig, frame):
            logger.info("Shutting down...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        while self.running:
            try:
                self.sock.settimeout(1.0)
                data, addr = self.sock.recvfrom(65536)
                self._process_data(data, addr)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Error receiving data: {e}")

        if self.sock:
            self.sock.close()
        logger.info(f"Processed {self.message_count} messages")

    def _process_data(self, data: bytes, addr: tuple):
        """Process incoming UDP data."""
        self.audio_buffer.extend(data)

        while len(self.audio_buffer) >= self.chunk_size:
            chunk = bytes(self.audio_buffer[:self.chunk_size])
            self.audio_buffer = self.audio_buffer[self.chunk_size:]

            samples = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
            messages = self.decoder.process(samples)

            for msg in messages:
                self.message_count += 1
                self._save_message(msg, addr)

    def _save_message(self, msg, addr: tuple):
        """Save decoded message to file."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = self.save_dir / f"dsc_{timestamp}_{self.message_count:04d}.json"

        data = {
            'timestamp': timestamp,
            'source': f"{addr[0]}:{addr[1]}",
            'format': msg.format_specifier,
            'category': msg.category,
            'mmsi_self': msg.mmsi_self,
            'mmsi_dest': msg.mmsi_dest,
            'tc1': msg.telecommand_1,
            'tc2': msg.telecommand_2,
            'nature': msg.nature_of_distress,
            'position': str(msg.position) if msg.position else None,
            'time_utc': msg.time_utc,
            'channel': msg.channel,
            'frequency': msg.frequency,
            'eos': msg.eos,
            'ecc': msg.ecc,
            'status': msg.status,
            'is_distress': msg.is_distress,
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved message to {filename}")
        if msg.is_distress:
            logger.warning(f"*** DISTRESS ALERT from MMSI {msg.mmsi_self} ***")


def main():
    parser = argparse.ArgumentParser(description='DSC UDP Monitor')
    parser.add_argument('--port', '-p', type=int, default=6000, help='UDP port to listen on')
    parser.add_argument('--sample-rate', '-r', type=int, default=INTERNAL_SAMPLE_RATE, help='Audio sample rate')
    parser.add_argument('--save-dir', '-s', default='./dsc_messages', help='Directory to save messages')
    parser.add_argument('--chunk-size', '-c', type=int, default=48000, help='Processing chunk size')
    args = parser.parse_args()

    monitor = DSCMonitor(
        port=args.port,
        sample_rate=args.sample_rate,
        save_dir=args.save_dir,
        chunk_size=args.chunk_size
    )

    monitor.start()


if __name__ == '__main__':
    main()
