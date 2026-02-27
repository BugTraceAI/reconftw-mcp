#!/usr/bin/env python3
"""MCP Server for reconFTW - AI Assistant Integration.

This module provides the Model Context Protocol (MCP) server that exposes
reconFTW's reconnaissance capabilities to AI assistants like Claude.

Supports two transports:
- STDIO (default): For local AI assistant integration (Claude Code, Cursor, etc.)
- SSE (--sse flag): For remote/network access (OpenClaw, remote MCP clients)

Usage:
    python mcp_server.py              # STDIO transport (default)
    python mcp_server.py --sse        # SSE transport on default port 8002
    python mcp_server.py --sse --port 9000  # Custom port

Author: BugTraceAI Team
Version: 1.0.0
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# Create FastMCP server instance
mcp_server = FastMCP(
    "reconftw-mcp",
    dependencies=["mcp", "pydantic"]
)

# Configuration
RECONFTW_DIR = Path(os.environ.get("RECONFTW_DIR", "/root/reconftw"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "/opt/reconftw/output"))
RECONFTW_SCRIPT = RECONFTW_DIR / "reconftw.sh"

# LAN-accessible transport security settings for SSE mode
_LAN_TRANSPORT_SECURITY = TransportSecuritySettings(
    enable_dns_rebinding_protection=False,
)


# Import tools and resources
import tools
import resources


def run_mcp_server(
    transport: str = "stdio",
    host: str = "0.0.0.0",
    port: int = 8002
) -> None:
    """Start the MCP server with the specified transport.
    
    Args:
        transport: Transport protocol - "stdio" (default) or "sse"
        host: Host to bind SSE server to (default: 0.0.0.0)
        port: Port for SSE server (default: 8002)
    """
    # Configure logging to stderr (stdout is used for JSON-RPC in STDIO mode)
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger("reconftw-mcp")
    
    # Configure transport and start server
    if transport == "sse":
        mcp_server.settings.host = host
        mcp_server.settings.port = port
        mcp_server.settings.transport_security = _LAN_TRANSPORT_SECURITY
        logger.info(f"Starting reconFTW MCP server on SSE at http://{host}:{port}/sse")
    else:
        logger.info("Starting reconFTW MCP server on STDIO transport")
    
    mcp_server.run(transport=transport)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="reconFTW MCP Server")
    parser.add_argument(
        "--sse",
        action="store_true",
        help="Use SSE transport instead of STDIO"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for SSE server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8002,
        help="Port for SSE server (default: 8002)"
    )
    
    args = parser.parse_args()
    
    run_mcp_server(
        transport="sse" if args.sse else "stdio",
        host=args.host,
        port=args.port
    )
