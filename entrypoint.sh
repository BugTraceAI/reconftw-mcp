#!/bin/bash
# reconFTW MCP Server Entrypoint
# Handles both MCP server mode and direct reconftw usage

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
RECONFTW_DIR="${RECONFTW_DIR:-/root/reconftw}"
OUTPUT_DIR="${OUTPUT_DIR:-/opt/reconftw/output}"
MCP_PORT="${MCP_PORT:-8002}"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Check if reconftw.sh exists
if [ ! -f "$RECONFTW_DIR/reconftw.sh" ]; then
    log_warn "reconftw.sh not found at $RECONFTW_DIR/reconftw.sh"
    log_info "Attempting to clone reconftw repository..."
    
    git clone --depth 1 https://github.com/six2dez/reconftw.git "$RECONFTW_DIR" 2>/dev/null || {
        log_error "Failed to clone reconftw repository"
        exit 1
    }
    
    cd "$RECONFTW_DIR"
    chmod +x reconftw.sh
    
    # Install reconftw dependencies
    if [ -f "install.sh" ]; then
        log_info "Installing reconftw dependencies..."
        ./install.sh 2>/dev/null || log_warn "Some dependencies may have failed to install"
    fi
fi

# Make reconftw executable
chmod +x "$RECONFTW_DIR/reconftw.sh" 2>/dev/null || true

# Handle different modes
case "$1" in
    mcp|mcp-server|--mcp)
        log_info "Starting reconFTW MCP Server..."
        log_info "Transport: ${2:-stdio}"
        log_info "Output directory: $OUTPUT_DIR"
        
        cd /opt/reconftw-mcp
        
        if [ "$2" = "--sse" ] || [ "$SSE_MODE" = "true" ]; then
            log_info "SSE mode enabled on port $MCP_PORT"
            exec python3 main.py --sse --port "$MCP_PORT" --host "0.0.0.0"
        else
            log_info "STDIO mode enabled"
            exec python3 main.py
        fi
        ;;
    
    reconftw|scan|--scan)
        shift
        log_info "Running reconftw directly..."
        cd "$RECONFTW_DIR"
        exec ./reconftw.sh "$@"
        ;;
    
    help|--help|-h)
        echo "reconFTW MCP Docker Container"
        echo ""
        echo "Usage:"
        echo "  docker run <image> [command] [options]"
        echo ""
        echo "Commands:"
        echo "  mcp, --mcp              Start MCP server (STDIO mode)"
        echo "  mcp --sse               Start MCP server (SSE mode)"
        echo "  reconftw [args]         Run reconftw.sh directly"
        echo "  help                    Show this help message"
        echo ""
        echo "Environment Variables:"
        echo "  RECONFTW_DIR            reconftw installation directory (default: /root/reconftw)"
        echo "  OUTPUT_DIR              Scan output directory (default: /opt/reconftw/output)"
        echo "  MCP_PORT                MCP SSE server port (default: 8002)"
        echo "  SSE_MODE                Set to 'true' to enable SSE mode by default"
        echo ""
        echo "Examples:"
        echo "  # Start MCP server (STDIO mode for Claude Code)"
        echo "  docker run -it reconftw-mcp mcp"
        echo ""
        echo "  # Start MCP server (SSE mode for remote access)"
        echo "  docker run -p 8002:8002 reconftw-mcp mcp --sse"
        echo ""
        echo "  # Run reconftw directly"
        echo "  docker run -v ./output:/opt/reconftw/output reconftw-mcp reconftw -d example.com"
        ;;
    
    *)
        # Default: start MCP server in STDIO mode
        log_info "No command specified, starting MCP server in STDIO mode..."
        log_info "Use 'help' command to see available options"
        
        cd /opt/reconftw-mcp
        exec python3 main.py
        ;;
esac
