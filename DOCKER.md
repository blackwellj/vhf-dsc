# Docker Development Setup

## Quick Start

```bash
# Build and run with hot-reload (no rebuild needed after code changes)
docker-compose up --build

# Run tests
docker-compose run --rm dsc python -m pytest tests/ -v

# Run CLI commands
docker-compose run --rm dsc python -m cli.main test
docker-compose run --rm dsc python -m cli.main encode --type distress -o test.wav
docker-compose run --rm dsc python -m cli.main decode test.wav
```

## Development Workflow

The `docker-compose.yml` mounts your local source code into the container, so:
- **No rebuild needed** after code changes
- **Hot-reload enabled** via `--reload` flag
- Just edit files and the container picks up changes automatically

## Production Build

```bash
# Build production image
docker build -t vhf-dsc .

# Run production container
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
