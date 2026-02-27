# reconFTW MCP Server

**Powered by [reconFTW](https://github.com/six2dez/reconftw) — Created by [@six2dez](https://github.com/six2dez)**

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/six2dez/reconftw)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-blue?style=for-the-badge)](https://modelcontextprotocol.io/)
[![Python](https://img.shields.io/badge/Python-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

**reconFTW MCP Server** is a wrapper for the incredibly powerful [reconFTW](https://github.com/six2dez/reconftw) reconnaissance framework. This project enables AI assistants to leverage the best-in-class automation created by **six2dez**.

## 🎯 Features

- **Full reconFTW Integration**: Access all reconFTW capabilities through MCP tools
- **Multiple Scan Modes**: Full, passive, subdomains, vulnerabilities, OSINT, and more
- **Real-time Status**: Monitor scan progress and get results on demand
- **Resource Access**: Access scan results as MCP resources
- **Dual Transport**: STDIO for local AI assistants, SSE for remote access
- **Docker Ready**: Pre-configured Docker and docker-compose setup

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/reconftw-mcp.git
cd reconftw-mcp

# Build and run (SSE mode)
docker-compose up -d

# MCP server will be available at http://localhost:8002/sse
```

### Option 2: Docker Direct

```bash
# Build the image
docker build -t reconftw-mcp .

# Run in SSE mode (for remote access)
docker run -p 8002:8002 -v reconftw-output:/opt/reconftw/output reconftw-mcp mcp --sse

# Run in STDIO mode (for Claude Code)
docker run -i -v reconftw-output:/opt/reconftw/output reconftw-mcp mcp
```

### Option 3: Local Installation

```bash
# Install reconFTW first
git clone --depth 1 https://github.com/six2dez/reconftw.git ~/reconftw
cd ~/reconftw && ./install.sh

# Install MCP server
pip install -r requirements.txt

# Run the MCP server
python mcp_server.py
```

## 🔧 Configuration

### Environment Variables

| Variable       | Description                     | Default                |
| -------------- | ------------------------------- | ---------------------- |
| `RECONFTW_DIR` | reconFTW installation directory | `/root/reconftw`       |
| `OUTPUT_DIR`   | Scan output directory           | `/opt/reconftw/output` |
| `MCP_PORT`     | MCP SSE server port             | `8002`                 |
| `SSE_MODE`     | Enable SSE mode by default      | `false`                |

### API Keys (Optional)

For enhanced reconnaissance, configure API keys in your environment or `.env` file:

```env
SHODAN_API_KEY=your_shodan_key
VIRUSTOTAL_API_KEY=your_vt_key
CENSYS_API_ID=your_censys_id
CENSYS_API_SECRET=your_censys_secret
# ... see reconFTW documentation for all supported APIs
```

## 📖 MCP Tools

### Scanning Tools

| Tool                 | Description                      |
| -------------------- | -------------------------------- |
| `start_recon`        | Start a full reconnaissance scan |
| `quick_recon`        | Fast passive reconnaissance      |
| `subdomain_enum`     | Subdomain enumeration            |
| `vulnerability_scan` | Vulnerability scanning           |
| `osint_scan`         | OSINT gathering                  |

### Status & Results

| Tool                 | Description                      |
| -------------------- | -------------------------------- |
| `get_scan_status`    | Check scan progress              |
| `list_results`       | List available scans             |
| `get_findings`       | Get scan findings                |
| `get_nuclei_results` | Get Nuclei vulnerability results |

### Control

| Tool        | Description         |
| ----------- | ------------------- |
| `stop_scan` | Stop a running scan |

## 🔌 Integration with AI Assistants

### Claude Code (STDIO Mode)

Add to your Claude Code configuration:

```json
{
  "mcpServers": {
    "reconftw": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "reconftw-output:/opt/reconftw/output",
        "reconftw-mcp",
        "mcp"
      ]
    }
  }
}
```

### Remote MCP Clients (SSE Mode)

Connect to `http://localhost:8002/sse` (or your server URL).

### Example Usage with Claude

```
User: Can you scan example.com for subdomains?

Claude: I'll start a subdomain enumeration scan for example.com.

[Claude calls subdomain_enum tool]

Claude: I've started scan #1 for example.com. Let me check the status...

[Claude calls get_scan_status tool]

Claude: The scan is running. I found 45 subdomains so far. Would you like me to wait for completion or get the current results?
```

## 📁 Project Structure

```
reconftw-mcp/
├── Dockerfile           # Docker image definition
├── docker-compose.yml   # Docker Compose configuration
├── mcp_server.py        # Main MCP server
├── tools.py             # MCP tools implementation
├── resources.py         # MCP resources implementation
├── entrypoint.sh        # Container entrypoint
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## 🛠️ Scan Modes

| Mode         | Description             | Duration  |
| ------------ | ----------------------- | --------- |
| `full`       | Complete reconnaissance | 1-4 hours |
| `passive`    | Passive sources only    | 10-30 min |
| `subdomains` | Subdomain enumeration   | 20-60 min |
| `vulns`      | Vulnerability scanning  | 30-90 min |
| `osint`      | OSINT gathering         | 15-45 min |
| `webs`       | Web analysis only       | 20-60 min |
| `hosts`      | Host analysis only      | 15-45 min |

## 📊 MCP Resources

Access scan data through MCP resources:

- `scan://list` - List all available scans
- `scan://results/{scan_name}` - Get results from a scan
- `scan://results/{scan_name}/{file_type}` - Get specific result file
- `config://reconftw` - Get reconFTW configuration
- `docs://tools` - Tool documentation
- `docs://modes` - Scan mode documentation

## ⚠️ Disclaimer

**IMPORTANT**: Usage of this tool for attacking targets without prior consent is illegal. It is the user's responsibility to obey all applicable laws. The developers assume no liability for misuse or damage caused by this tool.

Only use this tool:

- On systems you own
- With explicit permission from the owner
- In accordance with all applicable laws and regulations

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [reconFTW](https://github.com/six2dez/reconftw) - The amazing reconnaissance framework
- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol that makes AI integration possible
- [FastMCP](https://github.com/anthropics/fastmcp) - The fast MCP implementation

## 📮 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/reconftw-mcp/issues)
- **Discord**: [reconFTW Discord](https://discord.gg/R5DdXVEdTy)
- **Documentation**: [reconFTW Docs](https://docs.reconftw.com)
