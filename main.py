#!/usr/bin/env python3
"""Entry point for the reconFTW MCP server.

This file ensures there is only ONE FastMCP instance:
  1. Import mcp_server  → creates the FastMCP instance (mcp_server.mcp_server)
  2. Import tools       → registers @mcp_server.tool() decorators on that instance
  3. Import resources   → registers @mcp_server.resource() decorators on that instance
  4. Call run_mcp_server() to start serving

NOT importing these here and instead running mcp_server.py as __main__ would
cause a dual-import bug: Python loads mcp_server.py as '__main__', then when
tools.py does 'from mcp_server import mcp_server', Python loads the file again
as a second module ('mcp_server'), creating two distinct FastMCP instances.
Tools end up registered on the second instance while the first one serves
requests → tools/list returns [].
"""

import argparse
import mcp_server   # creates the FastMCP instance
import tools        # registers tool decorators on mcp_server.mcp_server
import resources    # registers resource decorators on mcp_server.mcp_server

from mcp_server import run_mcp_server

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="reconFTW MCP Server")
    parser.add_argument(
        "--sse",
        action="store_true",
        help="Use SSE transport instead of STDIO",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for SSE server (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8002,
        help="Port for SSE server (default: 8002)",
    )

    args = parser.parse_args()
    run_mcp_server(
        transport="sse" if args.sse else "stdio",
        host=args.host,
        port=args.port,
    )
