# Docker Setup

## Development (No Rebuild Needed)

The `docker-compose.yml` is configured for development with volume mounting:

```bash
# Start the web UI with hot-reload
docker-compose up

# Run tests
docker-compose run --rm dsc python -m pytest tests/ -v

# Run CLI commands
docker-compose run --rm dsc python -m cli.main test
docker-compose run --rm dsc python -m cli.main encode --type distress -o test.wav
docker-compose run --rm dsc python -m cli.main decode test.wav
```

**Key feature:** Source code is mounted as a volume, so code changes are picked up immediately without rebuilding the container.

## Production

```bash
# Build production image
docker build -t vhf-dsc .

# Run
docker run -p 8000:8000 vhf-dsc
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   RTL-Airband   │────▶│  UDP Stream     │
│   (Pi nodes)    │     │  (Port 6000)    │
└─────────────────┘     └────────┬────────┘
                                │
                     ┌──────────▼──────────┐
                     │   DSC Decoder       │
                     │   (FastAPI + CLI)   │
                     └──────────┬──────────┘
                                │
                     ┌──────────▼──────────┐
                     │   Web UI            │
                     │   (Port 8000)       │
                     └─────────────────────┘
```
