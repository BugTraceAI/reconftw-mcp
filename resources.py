"""MCP Resources for reconFTW - Exposes scan results as resources.

This module registers MCP resources on the FastMCP server instance,
allowing AI assistants to access scan results, configurations, and
documentation as resources.

Resources:
- scan://results/{scan_id} - Access scan results
- scan://list - List all available scans
- config://reconftw - reconFTW configuration
- docs://tools - Tool documentation

Author: BugTraceAI Team
Version: 1.0.0
"""

import json
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from mcp_server import mcp_server, OUTPUT_DIR, RECONFTW_DIR

logger = logging.getLogger("reconftw-mcp.resources")


@mcp_server.resource("scan://list")
def list_scans_resource() -> str:
    """List all available scan results as a resource.
    
    Returns:
        JSON string with list of available scans
    """
    scans = []
    
    if OUTPUT_DIR.exists():
        for scan_dir in sorted(OUTPUT_DIR.iterdir(), reverse=True):
            if not scan_dir.is_dir():
                continue
            
            scan_info = {
                "name": scan_dir.name,
                "path": str(scan_dir),
                "modified": datetime.fromtimestamp(
                    scan_dir.stat().st_mtime
                ).isoformat(),
            }
            
            # Check for key files
            key_files = [
                "subdomains.txt", "webs.txt", "vulnerabilities.txt",
                "urls.txt", "emails.txt", "nuclei.txt"
            ]
            
            available = []
            for kf in key_files:
                if (scan_dir / kf).exists():
                    available.append(kf)
            
            scan_info["available_files"] = available
            scans.append(scan_info)
    
    return json.dumps({
        "scans": scans,
        "total": len(scans),
        "output_dir": str(OUTPUT_DIR)
    }, indent=2)


@mcp_server.resource("scan://results/{scan_name}")
def get_scan_results_resource(scan_name: str) -> str:
    """Get results from a specific scan.
    
    Args:
        scan_name: Name of the scan directory
        
    Returns:
        JSON string with scan results summary
    """
    scan_dir = OUTPUT_DIR / scan_name
    
    if not scan_dir.exists():
        return json.dumps({
            "error": f"Scan '{scan_name}' not found",
            "available_scans": [d.name for d in OUTPUT_DIR.iterdir() if d.is_dir()]
        })
    
    results = {
        "scan_name": scan_name,
        "path": str(scan_dir),
        "files": {},
        "summary": {}
    }
    
    # Read key result files
    result_files = {
        "subdomains": "subdomains.txt",
        "webs": "webs.txt",
        "vulnerabilities": "vulnerabilities.txt",
        "urls": "urls.txt",
        "emails": "emails.txt",
        "nuclei": "nuclei.txt",
    }
    
    for key, filename in result_files.items():
        filepath = scan_dir / filename
        if filepath.exists():
            content = filepath.read_text().strip()
            lines = [l for l in content.split("\n") if l]
            results["files"][key] = {
                "file": filename,
                "count": len(lines),
                "preview": lines[:20]  # First 20 lines
            }
            results["summary"][f"{key}_count"] = len(lines)
    
    return json.dumps(results, indent=2)


@mcp_server.resource("scan://results/{scan_name}/{file_type}")
def get_scan_file_resource(scan_name: str, file_type: str) -> str:
    """Get a specific result file from a scan.
    
    Args:
        scan_name: Name of the scan directory
        file_type: Type of file (subdomains, webs, vulnerabilities, etc.)
        
    Returns:
        Content of the result file
    """
    file_map = {
        "subdomains": "subdomains.txt",
        "subs": "subdomains.txt",
        "webs": "webs.txt",
        "vulnerabilities": "vulnerabilities.txt",
        "vulns": "vulnerabilities.txt",
        "urls": "urls.txt",
        "emails": "emails.txt",
        "nuclei": "nuclei.txt",
    }
    
    filename = file_map.get(file_type, f"{file_type}.txt")
    filepath = OUTPUT_DIR / scan_name / filename
    
    if not filepath.exists():
        return json.dumps({
            "error": f"File '{filename}' not found in scan '{scan_name}'",
            "scan_dir": str(OUTPUT_DIR / scan_name)
        })
    
    content = filepath.read_text()
    
    # For large files, truncate and provide summary
    lines = content.strip().split("\n")
    if len(lines) > 500:
        return json.dumps({
            "file": filename,
            "total_lines": len(lines),
            "truncated": True,
            "preview": lines[:500],
            "message": f"File has {len(lines)} lines. Showing first 500."
        })
    
    return content


@mcp_server.resource("config://reconftw")
def get_reconftw_config_resource() -> str:
    """Get reconFTW configuration information.
    
    Returns:
        JSON string with configuration details
    """
    config_info = {
        "reconftw_dir": str(RECONFTW_DIR),
        "output_dir": str(OUTPUT_DIR),
        "reconftw_script": str(RECONFTW_DIR / "reconftw.sh"),
    }
    
    # Check for config file
    config_files = [
        RECONFTW_DIR / "reconftw.cfg",
        Path("/root/.config/reconftw/reconftw.cfg"),
    ]
    
    for cf in config_files:
        if cf.exists():
            config_info["config_file"] = str(cf)
            try:
                # Read and parse basic config
                content = cf.read_text()
                config_info["config_preview"] = content[:2000]
                if len(content) > 2000:
                    config_info["config_truncated"] = True
            except Exception as e:
                config_info["config_error"] = str(e)
            break
    
    return json.dumps(config_info, indent=2)


@mcp_server.resource("docs://tools")
def get_tools_documentation_resource() -> str:
    """Get documentation for available MCP tools.
    
    Returns:
        Markdown documentation for all available tools
    """
    docs = """# reconFTW MCP Tools Documentation

This MCP server exposes reconFTW reconnaissance capabilities to AI assistants.

## Available Tools

### Scanning Tools

#### `start_recon`
Start a comprehensive reconnaissance scan on a target.

**Parameters:**
- `target` (required): Target domain or IP/CIDR
- `mode` (optional): Scan mode - "full", "passive", "subdomains", "vulns", "osint", "webs", "hosts"
- `output_dir` (optional): Custom output directory
- `deep_scan` (optional): Enable deep scanning mode
- `extra_args` (optional): Additional command-line arguments

**Example:**
```json
{
    "target": "example.com",
    "mode": "full",
    "deep_scan": true
}
```

#### `quick_recon`
Fast passive reconnaissance using only passive sources.

**Parameters:**
- `target` (required): Target domain

#### `subdomain_enum`
Enumerate subdomains for a target domain.

**Parameters:**
- `target` (required): Target domain
- `brute_force` (optional): Enable DNS bruteforcing (default: true)

#### `vulnerability_scan`
Scan for web vulnerabilities (XSS, SSRF, SQLi, LFI, SSTI, etc.).

**Parameters:**
- `target` (required): Target domain or URL

#### `osint_scan`
Gather open source intelligence (emails, leaks, GitHub secrets, etc.).

**Parameters:**
- `target` (required): Target domain

### Status & Results Tools

#### `get_scan_status`
Check the status of a running or completed scan.

**Parameters:**
- `scan_id` (required): The scan ID to check

#### `list_results`
List all available scan results.

**Parameters:**
- `target` (optional): Filter by target domain

#### `get_findings`
Get findings from a scan.

**Parameters:**
- `scan_id` (required): The scan ID
- `finding_type` (optional): "all", "subdomains", "webs", "vulnerabilities", "emails", "urls"
- `limit` (optional): Maximum findings to return (default: 50)

#### `get_nuclei_results`
Get Nuclei vulnerability scanner results.

**Parameters:**
- `scan_id` (required): The scan ID
- `severity` (optional): Filter by severity - "critical", "high", "medium", "low", "info"

### Control Tools

#### `stop_scan`
Stop a running scan gracefully.

**Parameters:**
- `scan_id` (required): The scan ID to stop

## Available Resources

- `scan://list` - List all available scans
- `scan://results/{scan_name}` - Get results from a specific scan
- `scan://results/{scan_name}/{file_type}` - Get specific result file
- `config://reconftw` - Get reconFTW configuration
- `docs://tools` - This documentation

## Scan Modes

| Mode | Description | Duration |
|------|-------------|----------|
| `full` | Complete reconnaissance | 1-4 hours |
| `passive` | Passive sources only | 10-30 min |
| `subdomains` | Subdomain enumeration | 20-60 min |
| `vulns` | Vulnerability scanning | 30-90 min |
| `osint` | OSINT gathering | 15-45 min |
| `webs` | Web analysis only | 20-60 min |
| `hosts` | Host analysis only | 15-45 min |

## Best Practices

1. Start with `quick_recon` for initial assessment
2. Use `get_scan_status` to monitor progress
3. Use `get_findings` with `finding_type="all"` for overview
4. Use `list_results` to find previous scans
5. Always verify targets before scanning
"""
    return docs


@mcp_server.resource("docs://modes")
def get_scan_modes_resource() -> str:
    """Get documentation for scan modes.
    
    Returns:
        JSON string with scan mode documentation
    """
    modes = {
        "full": {
            "description": "Complete reconnaissance including all phases",
            "estimated_duration": "1-4 hours",
            "includes": [
                "OSINT gathering",
                "Subdomain enumeration (passive + active)",
                "DNS analysis",
                "Port scanning",
                "Web probing",
                "Vulnerability scanning",
                "Screenshot capture"
            ]
        },
        "passive": {
            "description": "Passive reconnaissance only (no direct target contact)",
            "estimated_duration": "10-30 minutes",
            "includes": [
                "Passive subdomain enumeration",
                "Certificate transparency logs",
                "OSINT from public sources",
                "No active scanning"
            ]
        },
        "subdomains": {
            "description": "Subdomain enumeration focus",
            "estimated_duration": "20-60 minutes",
            "includes": [
                "Passive subdomain sources",
                "DNS bruteforcing",
                "Permutation attacks",
                "DNS zone transfers",
                "Subdomain takeover checks"
            ]
        },
        "vulns": {
            "description": "Vulnerability scanning focus",
            "estimated_duration": "30-90 minutes",
            "includes": [
                "Nuclei templates",
                "XSS scanning",
                "SQLi detection",
                "SSRF testing",
                "LFI/RFI checks",
                "SSTI detection"
            ]
        },
        "osint": {
            "description": "Open Source Intelligence gathering",
            "estimated_duration": "15-45 minutes",
            "includes": [
                "Email harvesting",
                "Credential leak search",
                "GitHub repository analysis",
                "Cloud storage enumeration",
                "Document metadata extraction",
                "API key leak detection"
            ]
        },
        "webs": {
            "description": "Web application analysis",
            "estimated_duration": "20-60 minutes",
            "includes": [
                "Web probing",
                "JavaScript analysis",
                "URL discovery",
                "Directory fuzzing",
                "Parameter discovery",
                "Screenshot capture"
            ]
        },
        "hosts": {
            "description": "Host and infrastructure analysis",
            "estimated_duration": "15-45 minutes",
            "includes": [
                "IP geolocation",
                "CDN detection",
                "WAF detection",
                "Port scanning",
                "Service fingerprinting",
                "Cloud provider detection"
            ]
        }
    }
    
    return json.dumps(modes, indent=2)
