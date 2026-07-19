# Server Deployment Guide

## Quick Start

```bash
# Clone the repo
git clone https://github.com/blackwellj/vhf-dsc.git
cd vhf-dsc

# Start the monitor (listens on UDP 5555, web UI on 8000)
docker-compose -f docker-compose.server.yml up -d

# View logs
docker-compose -f docker-compose.server.yml logs -f

# Stop
docker-compose -f docker-compose.server.yml down
```

## Configuration

Edit `docker-compose.server.yml` to change:
- `UDP_PORT` - Port for RTL-Airband audio (default: 5555)
- `SAMPLE_RATE` - Audio sample rate (default: 16000)
- `SAVE_DIR` - Where to save decoded messages

## RTL-Airband Setup

Configure RTL-Airband to send audio to the DSC monitor:

```
rtl_airband -f
```

Or use the UDP relay script:
```bash
python scripts/udp_relay.py --input-port RTL_AIRBAND_PORT --output-port 5555
```

## Viewing Decoded Messages

Messages are saved as JSON files in `./dsc_messages/`:

```bash
# List recent messages
ls -lt dsc_messages/ | head

# View a message
cat dsc_messages/dsc_20240101_120000_0001.json

# View distress alerts only
grep -l "distress" dsc_messages/*.json
```

## Web UI

Access the web interface at `http://YOUR_SERVER_IP:8000`

## Manual Setup (No Docker)

```bash
# Install dependencies
pip install -e ".[dev]"

# Start monitor
python -m cli.monitor_server --port 5555 --sample-rate 16000 --save-dir ./dsc_messages

# Start web UI (in another terminal)
uvicorn web.app:app --host 0.0.0.0 --port 8000
```
