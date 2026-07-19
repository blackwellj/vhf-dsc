# VHF DSC Encoder/Decoder

ITU-R M.493-16 compliant VHF Digital Selective Calling (DSC) encoder and decoder.

## Overview

This project provides a complete DSC implementation for VHF maritime radio, including:

- **Decoder**: Processes audio from RTL-SDR dongles (via RTL-Airband UDP stream) or uploaded audio files
- **Encoder**: Generates test DSC messages as WAV or raw IQ files, with UDP replay capability
- **Web UI**: FastAPI-based dashboard for monitoring, encoding, and decoding
- **CLI**: Command-line tools for all operations

## Technical Specifications

| Parameter | Value |
|-----------|-------|
| Mark frequency | 1300 Hz |
| Space frequency | 2100 Hz |
| Baud rate | 1200 |
| Internal sample rate | 16000 Hz |
| UDP format | PCM16 mono |
| Character encoding | 10-bit ITU Table A1-1 |
| Error correction | Even vertical parity (CRC-7) |

## Quick Start

### Generate test messages

```bash
# Generate a single distress message
python -m src.cli.main encode --type distress --mmsi 234567890 -o distress.wav

# Generate all message types
python -m src.cli.main encode --type test -o test.wav
python -m src.cli.main encode --type safety -o safety.wav
python -m src.cli.main encode --type urgency -o urgency.wav
python -m src.cli.main encode --type routine -o routine.wav

# Generate full test suite with channel impairments
python -m src.cli.main encode --type distress --suite --suite-dir ./test_suite
```

### Decode audio files

```bash
# Decode a WAV file
python -m src.cli.main decode distress.wav

# Decode with JSON output
python -m src.cli.main decode distress.wav --json

# Decode raw audio
python -m src.cli.main decode signal.raw --format raw --sample-rate 16000
```

### Monitor live UDP stream

```bash
# Listen for DSC messages on UDP port 6000
python -m src.cli.main monitor --port 6000
```

### Replay audio as UDP stream

```bash
# Send audio file as UDP stream (instant)
python -m src.cli.main replay distress.wav --host 127.0.0.1 --port 6000

# Send at real-time speed
python -m src.cli.main replay distress.wav --host 127.0.0.1 --port 6000 --realtime

# Loop playback
python -m src.cli.main replay distress.wav --host 127.0.0.1 --port 6000 --loop
```

### Run self-test

```bash
python -m src.cli.main test
```

### Start web UI

```bash
python -m uvicorn web.app:app --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000 in your browser.

## Supported Message Types

- Distress alerts (all nature codes)
- Distress acknowledgments
- All-ships safety calls
- All-ships urgency calls
- Individual routine calls
- Group calls
- Geographic area calls
- Test messages

## Project Structure

```
src/vhf_dsc/
├── protocol/          # ITU-R M.493-16 protocol layer
│   ├── constants.py   # Frequencies, timings
│   ├── characters.py  # 10-bit character set (Table A1-1)
│   ├── error_correction.py  # ECC (even vertical parity)
│   ├── message.py     # DSC message structures
│   ├── symbols.py     # All ITU symbol values (Table A1-3)
│   ├── mmsi.py        # MMSI handling
│   └── position.py    # Position encoding
├── dsp/               # Signal processing
│   ├── goertzel.py    # Tone detection
│   ├── vhf_fsk.py     # FSK mod/demod
│   ├── filters.py     # Digital filters
│   ├── pll.py         # Symbol sync PLL
│   ├── synchronizer.py # Bit synchronizer
│   └── signal_quality.py
├── decoder/           # Decode pipeline
│   ├── pipeline.py    # Main orchestrator
│   ├── demodulator.py # FSK demodulation
│   ├── parser.py      # Message parsing
│   ├── validator.py   # ECC validation
│   └── clusterer.py   # Multi-window clustering
├── encoder/           # Message generation
│   ├── builder.py     # Fluent message builder
│   ├── serializer.py  # Symbol serialization + time diversity
│   ├── modulator.py   # FSK modulation + channel simulator
│   ├── test_messages.py # Pre-built test messages
│   └── channel_simulator.py # Radio channel impairments
└── io/                # Audio I/O
    ├── wav.py         # WAV read/write
    ├── raw.py         # Raw IQ read/write
    ├── udp_stream.py  # UDP stream handling
    └── file_upload.py # File upload handler

src/cli/               # Command-line tools
web/                   # FastAPI web interface
tests/                 # Test suite
scripts/               # Utility scripts
```

## Compliance

Implemented per:
- **ITU-R M.493-16** (2023) - Digital selective-calling system
- **ITU-R M.541-11** (2023) - Operational procedures

## Channel Simulator

The encoder includes a realistic radio channel simulator:

```bash
# Generate with specific channel model
python -m src.cli.main encode --type distress --channel good -o distress_good.wav
python -m src.cli.main encode --type distress --channel moderate -o distress_moderate.wav
python -m src.cli.main encode --type distress --channel poor -o distress_poor.wav
python -m src.cli.main encode --type distress --channel marginal -o distress_marginal.wav

# Generate with custom SNR
python -m src.cli.main encode --type distress --snr 15 -o distress_15db.wav

# Generate with reproducible results
python -m src.cli.main encode --type distress --channel moderate --seed 42 -o distress.wav
```

Impairments simulated:
- AWGN (Additive White Gaussian Noise)
- Multipath fading (Rayleigh/Rician)
- Doppler shift (vessel movement)
- Phase noise/jitter
- Frequency offset
- Amplitude distortion
- Impulse noise
- Adjacent channel interference
- Co-channel interference
- Bandpass filtering
- Selective fading
- Atmospheric noise

## License

MIT
