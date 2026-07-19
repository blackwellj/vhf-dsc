"""Generate test audio samples for DSC testing."""

import sys
sys.path.insert(0, ".")

from vhf_dsc.encoder import TestMessageGenerator, DSCModulator
from vhf_dsc.io.wav import write_wav_normalized
from vhf_dsc.protocol.constants import INTERNAL_SAMPLE_RATE


def main():
    modulator = DSCModulator(INTERNAL_SAMPLE_RATE)
    messages = TestMessageGenerator.all_messages()

    for msg in messages:
        name = f"{msg.format_specifier.name.lower() if msg.format_specifier else 'unknown'}"
        audio = modulator.modulate(msg)
        filepath = f"tests/fixtures/{name}.wav"
        write_wav_normalized(filepath, audio, INTERNAL_SAMPLE_RATE)
        print(f"Generated {filepath} ({len(audio) / INTERNAL_SAMPLE_RATE:.2f}s)")

    print(f"\nGenerated {len(messages)} test samples")


if __name__ == "__main__":
    main()
