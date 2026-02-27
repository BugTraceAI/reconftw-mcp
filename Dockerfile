# reconFTW MCP Server
# Extends the official reconftw image with MCP (Model Context Protocol) support
# Allows AI assistants to control reconftw scans programmatically

FROM six2dez/reconftw:main

LABEL maintainer="BugTraceAI Team"
LABEL description="reconFTW with MCP server for AI assistant integration"
LABEL version="1.0.0"

# Install Python and required dependencies for MCP
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment for MCP dependencies
RUN python3 -m venv /opt/mcp-venv
ENV PATH="/opt/mcp-venv/bin:$PATH"

# Install MCP dependencies
RUN pip install --no-cache-dir \
    mcp[cli]>=1.0.0 \
    fastmcp>=0.1.0 \
    pydantic>=2.0.0

# Create MCP server directory
WORKDIR /opt/reconftw-mcp

# Copy MCP server files
COPY mcp_server.py .
COPY tools.py .
COPY resources.py .
COPY requirements.txt .

# Install any additional requirements
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true

# Create output directory for scan results
RUN mkdir -p /opt/reconftw/output

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose MCP SSE port
EXPOSE 8002

# Health check (handles exit code 28 as success since SSE streams timeout)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -sS -m 2 http://localhost:8002/sse >/dev/null; res=$?; [ $res -eq 0 ] || [ $res -eq 28 ] || exit 1

# Default to MCP server mode
ENTRYPOINT ["/entrypoint.sh"]
CMD ["mcp"]
