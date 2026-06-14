# Armarius Container Deployment Guide

## Prerequisites

- **Podman** (or Docker): Container runtime
- **podman-compose** (optional): For compose file support

```bash
# macOS
brew install podman podman-compose

# Linux
sudo apt install podman podman-compose
```

## Quick Start

### Option 1: Using helper script (Recommended)

```bash
# Build image
./podman.sh build

# Run with default settings
./podman.sh run

# Run with custom library path
./podman.sh run --library ~/my-papers --port 8080

# View logs
./podman.sh logs

# Stop container
./podman.sh stop

# Check status
./podman.sh status

# Clean up
./podman.sh clean
```

### Option 2: Using podman-compose

```bash
# Set library path (optional)
export ARMARIUS_LIBRARY_PATH=~/my-papers

# Start service
podman-compose up -d

# View logs
podman-compose logs -f

# Stop service
podman-compose down
```

### Option 3: Manual podman commands

```bash
# Build image
podman build -t armarius:latest -f Containerfile .

# Run container
podman run -d \
  --name armarius \
  -p 8501:8501 \
  -v ~/Documents/papers:/library:Z \
  -v ~/.armarius:/root/.armarius:Z \
  -e ARMARIUS_LIBRARY_ROOT=/library \
  --restart unless-stopped \
  armarius:latest

# View logs
podman logs -f armarius

# Stop container
podman stop armarius

# Remove container
podman rm armarius
```

## Configuration

### Environment Variables

- `ARMARIUS_LIBRARY_ROOT`: PDF library path (default: `/library`)
- `ARMARIUS_WEB_PORT`: Web UI port (default: `8501`)

### Volume Mounts

1. **Library folder**: `-v ~/Documents/papers:/library:Z`
   - Mount your PDF collection here
   - The `:Z` flag enables SELinux relabeling (Linux only)

2. **Config folder**: `-v ~/.armarius:/root/.armarius:Z`
   - Persists Armarius configuration
   - Contains `config.yaml` and logs

## Using uv for Development

This container uses `uv` for fast dependency installation:

```bash
# Local development with uv
uv pip install -e .

# Update dependencies
uv pip compile pyproject.toml -o requirements.txt
uv pip sync requirements.txt
```

## Accessing the Application

Once running, access Armarius at:
- **Web UI**: http://localhost:8501

## Troubleshooting

### Port already in use

```bash
# Change port
./podman.sh run --port 8080

# Or find and kill process
lsof -ti:8501 | xargs kill
```

### Permission issues (Linux)

If you encounter permission errors with volumes:

```bash
# Use :Z flag for SELinux
-v ~/papers:/library:Z

# Or disable SELinux temporarily
sudo setenforce 0
```

### Container won't start

```bash
# Check logs
./podman.sh logs

# Or
podman logs armarius
```

### Health check failing

```bash
# Check if Streamlit is running inside container
./podman.sh shell
curl http://localhost:8501/_stcore/health
```

## Multi-architecture Builds

Build for different platforms:

```bash
# ARM64 (Apple Silicon, ARM servers)
podman build --platform linux/arm64 -t armarius:arm64 .

# AMD64 (Intel/AMD)
podman build --platform linux/amd64 -t armarius:amd64 .

# Multi-arch manifest
podman manifest create armarius:latest
podman manifest add armarius:latest armarius:arm64
podman manifest add armarius:latest armarius:amd64
```

## Production Deployment

### Systemd service (Linux)

```bash
# Generate systemd unit file
podman generate systemd --name armarius --files

# Move to systemd directory
sudo mv container-armarius.service /etc/systemd/system/

# Enable and start
sudo systemctl enable --now container-armarius.service
```

### Resource limits

```bash
podman run -d \
  --name armarius \
  --memory 1g \
  --cpus 2 \
  -p 8501:8501 \
  -v ~/papers:/library:Z \
  armarius:latest
```

## Updating

```bash
# Pull latest code
git pull

# Rebuild image
./podman.sh build

# Restart container
./podman.sh restart
```

## Security Notes

- Container runs as `root` by default (Streamlit requirement)
- Use `:Z` flag for SELinux systems
- Health check verifies Streamlit is responsive
- `--restart unless-stopped` ensures auto-restart

## See Also

- [Podman Documentation](https://docs.podman.io/)
- [Streamlit Deployment Guide](https://docs.streamlit.io/deploy)
- [uv Documentation](https://github.com/astral-sh/uv)
