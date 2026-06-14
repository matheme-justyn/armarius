#!/bin/bash
# Armarius Podman Helper Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="armarius:latest"
CONTAINER_NAME="armarius"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

show_help() {
    cat << EOF
Armarius Podman Helper

Usage: $0 [COMMAND] [OPTIONS]

Commands:
  build         Build Armarius container image
  run           Run Armarius container
  start         Start existing Armarius container
  stop          Stop Armarius container
  restart       Restart Armarius container
  logs          Show container logs
  shell         Open shell in running container
  remove        Remove container
  clean         Remove container and image
  status        Show container status
  help          Show this help message

Options for 'run':
  --library PATH    PDF library path (default: ~/Documents/papers)
  --port PORT       Web UI port (default: 8501)
  --name NAME       Container name (default: armarius)

Examples:
  # Build image
  $0 build

  # Run with custom library path
  $0 run --library ~/my-papers

  # Run with custom port
  $0 run --port 8080

  # View logs
  $0 logs

  # Stop and remove
  $0 clean

EOF
}

build_image() {
    print_info "Building Armarius image with uv..."
    cd "$SCRIPT_DIR"
    
    if podman build -t "$IMAGE_NAME" -f Containerfile .; then
        print_success "Image built successfully: $IMAGE_NAME"
        podman images | grep armarius
    else
        print_error "Build failed"
        exit 1
    fi
}

run_container() {
    # Parse arguments
    LIBRARY_PATH="$HOME/Documents/papers"
    WEB_PORT=8501
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --library)
                LIBRARY_PATH="$2"
                shift 2
                ;;
            --port)
                WEB_PORT="$2"
                shift 2
                ;;
            --name)
                CONTAINER_NAME="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    # Check if library path exists
    if [ ! -d "$LIBRARY_PATH" ]; then
        print_warning "Library path does not exist: $LIBRARY_PATH"
        read -p "Create it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            mkdir -p "$LIBRARY_PATH"
            print_success "Created library directory"
        else
            print_error "Aborted"
            exit 1
        fi
    fi
    
    # Check if container already exists
    if podman container exists "$CONTAINER_NAME"; then
        print_warning "Container '$CONTAINER_NAME' already exists"
        read -p "Remove and recreate? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            podman rm -f "$CONTAINER_NAME"
        else
            print_info "Use '$0 start' to start existing container"
            exit 0
        fi
    fi
    
    print_info "Starting Armarius container..."
    print_info "Library: $LIBRARY_PATH"
    print_info "Port: $WEB_PORT"
    
    podman run -d \
        --name "$CONTAINER_NAME" \
        -p "$WEB_PORT:8501" \
        -v "$LIBRARY_PATH:/library:Z" \
        -v "$HOME/.armarius:/root/.armarius:Z" \
        -e "ARMARIUS_LIBRARY_ROOT=/library" \
        -e "ARMARIUS_WEB_PORT=8501" \
        --restart unless-stopped \
        "$IMAGE_NAME"
    
    print_success "Container started: $CONTAINER_NAME"
    print_info "Web UI: http://localhost:$WEB_PORT"
    print_info ""
    print_info "Commands:"
    print_info "  View logs:  $0 logs"
    print_info "  Stop:       $0 stop"
    print_info "  Shell:      $0 shell"
}

start_container() {
    if podman container exists "$CONTAINER_NAME"; then
        podman start "$CONTAINER_NAME"
        print_success "Container started"
        show_url
    else
        print_error "Container '$CONTAINER_NAME' does not exist. Run '$0 run' first."
        exit 1
    fi
}

stop_container() {
    if podman container exists "$CONTAINER_NAME"; then
        podman stop "$CONTAINER_NAME"
        print_success "Container stopped"
    else
        print_warning "Container '$CONTAINER_NAME' not found"
    fi
}

restart_container() {
    if podman container exists "$CONTAINER_NAME"; then
        podman restart "$CONTAINER_NAME"
        print_success "Container restarted"
        show_url
    else
        print_error "Container '$CONTAINER_NAME' does not exist"
        exit 1
    fi
}

show_logs() {
    if podman container exists "$CONTAINER_NAME"; then
        podman logs -f "$CONTAINER_NAME"
    else
        print_error "Container '$CONTAINER_NAME' does not exist"
        exit 1
    fi
}

open_shell() {
    if podman container exists "$CONTAINER_NAME"; then
        print_info "Opening shell in container..."
        podman exec -it "$CONTAINER_NAME" /bin/bash
    else
        print_error "Container '$CONTAINER_NAME' does not exist or not running"
        exit 1
    fi
}

remove_container() {
    if podman container exists "$CONTAINER_NAME"; then
        print_warning "Removing container: $CONTAINER_NAME"
        podman rm -f "$CONTAINER_NAME"
        print_success "Container removed"
    else
        print_info "Container '$CONTAINER_NAME' not found"
    fi
}

clean_all() {
    remove_container
    
    if podman image exists "$IMAGE_NAME"; then
        print_warning "Removing image: $IMAGE_NAME"
        podman rmi "$IMAGE_NAME"
        print_success "Image removed"
    else
        print_info "Image '$IMAGE_NAME' not found"
    fi
}

show_status() {
    print_info "Armarius Container Status"
    echo ""
    
    if podman container exists "$CONTAINER_NAME"; then
        STATUS=$(podman inspect --format='{{.State.Status}}' "$CONTAINER_NAME")
        print_info "Container: $CONTAINER_NAME ($STATUS)"
        
        if [ "$STATUS" = "running" ]; then
            PORT=$(podman port "$CONTAINER_NAME" 8501 | cut -d':' -f2)
            print_info "Web UI: http://localhost:$PORT"
            
            # Show resource usage
            echo ""
            podman stats --no-stream "$CONTAINER_NAME"
        fi
    else
        print_warning "Container not found"
    fi
    
    echo ""
    if podman image exists "$IMAGE_NAME"; then
        print_info "Image exists: $IMAGE_NAME"
        podman images | grep armarius
    else
        print_warning "Image not built yet. Run '$0 build'"
    fi
}

show_url() {
    if podman container exists "$CONTAINER_NAME"; then
        PORT=$(podman port "$CONTAINER_NAME" 8501 2>/dev/null | cut -d':' -f2 || echo "8501")
        print_info "Web UI: http://localhost:$PORT"
    fi
}

# Main command dispatcher
case "${1:-help}" in
    build)
        build_image
        ;;
    run)
        shift
        run_container "$@"
        ;;
    start)
        start_container
        ;;
    stop)
        stop_container
        ;;
    restart)
        restart_container
        ;;
    logs)
        show_logs
        ;;
    shell)
        open_shell
        ;;
    remove)
        remove_container
        ;;
    clean)
        clean_all
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
