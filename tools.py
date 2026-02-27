"""MCP Tools for reconFTW - Exposes reconnaissance capabilities to AI assistants.

This module registers MCP tools on the FastMCP server instance.
Each tool wraps reconftw.sh commands for AI assistant use.

Tools:
- start_recon: Start a full reconnaissance scan
- quick_recon: Quick reconnaissance (passive only)
- subdomain_enum: Subdomain enumeration only
- vulnerability_scan: Vulnerability scanning only
- osint_scan: OSINT gathering only
- get_scan_status: Check scan progress
- list_results: List available scan results
- get_findings: Get findings from a scan
- stop_scan: Stop a running scan

Author: BugTraceAI Team
Version: 1.0.0
"""

import os
import sys
import json
import asyncio
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from mcp_server import mcp_server, RECONFTW_SCRIPT, OUTPUT_DIR

logger = logging.getLogger("reconftw-mcp.tools")


class ScanMode(str, Enum):
    """reconFTW scan modes."""
    FULL = "full"
    PASSIVE = "passive"
    SUBDOMAINS = "subdomains"
    VULNS = "vulns"
    OSINT = "osint"
    WEBS = "webs"
    HOSTS = "hosts"


class ScanState:
    """Track active scans."""
    active_scans: Dict[int, Dict[str, Any]] = {}
    _counter = 0
    
    @classmethod
    def create_scan(cls, target: str, mode: str) -> int:
        cls._counter += 1
        scan_id = cls._counter
        cls.active_scans[scan_id] = {
            "id": scan_id,
            "target": target,
            "mode": mode,
            "status": "initializing",
            "started_at": datetime.now().isoformat(),
            "process": None,
            "output_dir": None,
        }
        return scan_id
    
    @classmethod
    def get_scan(cls, scan_id: int) -> Optional[Dict[str, Any]]:
        return cls.active_scans.get(scan_id)
    
    @classmethod
    def update_scan(cls, scan_id: int, **kwargs):
        if scan_id in cls.active_scans:
            cls.active_scans[scan_id].update(kwargs)


@mcp_server.tool()
async def start_recon(
    target: str,
    mode: str = "full",
    output_dir: Optional[str] = None,
    deep_scan: bool = False,
    extra_args: Optional[str] = None
) -> Dict[str, Any]:
    """Start a reconnaissance scan on a target domain or IP.
    
    This tool launches reconFTW to perform comprehensive reconnaissance
    including subdomain enumeration, vulnerability scanning, and OSINT.
    
    Args:
        target: Target domain (e.g., "example.com") or IP/CIDR range
        mode: Scan mode - "full" (default), "passive", "subdomains", 
              "vulns", "osint", "webs", "hosts"
        output_dir: Custom output directory (optional, auto-generated if not provided)
        deep_scan: Enable deep scanning mode (takes longer, more thorough)
        extra_args: Additional arguments to pass to reconftw.sh
        
    Returns:
        Dictionary with scan_id, status, and output directory path
        
    Example:
        result = await start_recon("example.com", mode="passive")
    """
    try:
        # Validate target
        if not target or len(target) < 3:
            return {"error": "Invalid target", "status": "failed"}
        
        # Create scan tracking
        scan_id = ScanState.create_scan(target, mode)
        
        # Prepare output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_target = target.replace("/", "_").replace(":", "_")
        scan_output_dir = Path(output_dir) if output_dir else OUTPUT_DIR / f"{safe_target}_{timestamp}"
        scan_output_dir.mkdir(parents=True, exist_ok=True)
        
        ScanState.update_scan(scan_id, output_dir=str(scan_output_dir), status="starting")
        
        # Build command
        cmd = [str(RECONFTW_SCRIPT)]
        
        # Add mode-specific arguments
        mode_args = {
            "full": ["-d", target],
            "passive": ["-d", target, "--deep"],
            "subdomains": ["-d", target, "-s"],
            "vulns": ["-d", target, "-v"],
            "osint": ["-d", target, "--osint"],
            "webs": ["-d", target, "-w"],
            "hosts": ["-d", target, "-h"],
        }
        
        if mode in mode_args:
            cmd.extend(mode_args[mode])
        else:
            cmd.extend(["-d", target])  # Default to full scan
        
        if deep_scan:
            cmd.append("--deep")
        
        if extra_args:
            cmd.extend(extra_args.split())
        
        # Set environment for non-interactive mode
        env = os.environ.copy()
        env["DEEP"] = "true" if deep_scan else "false"
        env["RECONFTW_OUTPUT"] = str(scan_output_dir)
        
        logger.info(f"Starting scan {scan_id}: {' '.join(cmd)}")
        
        # Start the scan process
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=str(scan_output_dir)
        )
        
        ScanState.update_scan(
            scan_id,
            process=process,
            status="running",
            pid=process.pid
        )
        
        # Start background task to monitor process
        asyncio.create_task(_monitor_scan(scan_id, process))
        
        return {
            "scan_id": scan_id,
            "status": "started",
            "target": target,
            "mode": mode,
            "output_dir": str(scan_output_dir),
            "pid": process.pid,
            "message": f"Reconnaissance scan started for {target}"
        }
        
    except Exception as e:
        logger.exception(f"Failed to start scan for {target}")
        return {
            "error": str(e),
            "status": "failed",
            "message": f"Failed to start scan: {str(e)}"
        }


async def _monitor_scan(scan_id: int, process):
    """Monitor a running scan process."""
    try:
        stdout, stderr = await process.communicate()
        
        scan = ScanState.get_scan(scan_id)
        if not scan:
            return
        
        output_dir = Path(scan["output_dir"]) if scan.get("output_dir") else None
        
        # Save output logs
        if output_dir and stdout:
            (output_dir / "stdout.log").write_bytes(stdout)
        if output_dir and stderr:
            (output_dir / "stderr.log").write_bytes(stderr)
        
        # Update status based on return code
        if process.returncode == 0:
            ScanState.update_scan(scan_id, status="completed", return_code=0)
            logger.info(f"Scan {scan_id} completed successfully")
        else:
            ScanState.update_scan(
                scan_id,
                status="failed",
                return_code=process.returncode,
                error=stderr.decode() if stderr else "Unknown error"
            )
            logger.error(f"Scan {scan_id} failed with code {process.returncode}")
            
    except Exception as e:
        logger.exception(f"Error monitoring scan {scan_id}")
        ScanState.update_scan(scan_id, status="error", error=str(e))


@mcp_server.tool()
async def quick_recon(target: str) -> Dict[str, Any]:
    """Perform quick passive reconnaissance on a target.
    
    Fast reconnaissance using only passive sources (no direct contact
    with the target). Great for initial assessment.
    
    Args:
        target: Target domain to scan
        
    Returns:
        Dictionary with scan_id and initial status
    """
    return await start_recon(target, mode="passive")


@mcp_server.tool()
async def subdomain_enum(target: str, brute_force: bool = True) -> Dict[str, Any]:
    """Enumerate subdomains for a target domain.
    
    Discovers subdomains using passive sources, certificate transparency,
    and optional DNS bruteforcing.
    
    Args:
        target: Target domain (e.g., "example.com")
        brute_force: Enable DNS bruteforcing (slower but more thorough)
        
    Returns:
        Dictionary with scan_id and status
    """
    extra_args = "--brute" if brute_force else None
    return await start_recon(target, mode="subdomains", extra_args=extra_args)


@mcp_server.tool()
async def vulnerability_scan(target: str) -> Dict[str, Any]:
    """Scan for vulnerabilities on a target.
    
    Performs vulnerability scanning including XSS, SSRF, SQLi, LFI,
    SSTI, and other common web vulnerabilities.
    
    Args:
        target: Target domain or URL
        
    Returns:
        Dictionary with scan_id and status
    """
    return await start_recon(target, mode="vulns")


@mcp_server.tool()
async def osint_scan(target: str) -> Dict[str, Any]:
    """Perform OSINT (Open Source Intelligence) gathering.
    
    Gathers open source intelligence including:
    - Email addresses and credentials from leaks
    - Metadata from documents
    - API keys and secrets in public sources
    - GitHub repository analysis
    - Cloud storage enumeration
    
    Args:
        target: Target domain
        
    Returns:
        Dictionary with scan_id and status
    """
    return await start_recon(target, mode="osint")


@mcp_server.tool()
async def get_scan_status(scan_id: int) -> Dict[str, Any]:
    """Get the current status of a reconnaissance scan.
    
    Args:
        scan_id: The ID of the scan to check
        
    Returns:
        Dictionary with scan status, progress, and findings summary
    """
    scan = ScanState.get_scan(scan_id)
    if not scan:
        return {"error": f"Scan {scan_id} not found", "scan_id": scan_id}
    
    result = {
        "scan_id": scan_id,
        "target": scan.get("target"),
        "mode": scan.get("mode"),
        "status": scan.get("status"),
        "started_at": scan.get("started_at"),
        "pid": scan.get("pid"),
    }
    
    # Check output directory for progress
    output_dir = Path(scan["output_dir"]) if scan.get("output_dir") else None
    if output_dir and output_dir.exists():
        result["output_dir"] = str(output_dir)
        
        # Count result files
        txt_files = list(output_dir.glob("**/*.txt"))
        result["files_created"] = len(txt_files)
        
        # Check for subdomains
        subs_file = output_dir / "subdomains.txt"
        if subs_file.exists():
            subs = subs_file.read_text().strip().split("\n")
            result["subdomains_found"] = len([s for s in subs if s])
    
    return result


@mcp_server.tool()
async def list_results(target: Optional[str] = None) -> Dict[str, Any]:
    """List available scan results.
    
    Args:
        target: Filter by target domain (optional)
        
    Returns:
        Dictionary with list of available scan results
    """
    results = []
    
    if not OUTPUT_DIR.exists():
        return {"results": [], "message": "No results directory found"}
    
    for scan_dir in sorted(OUTPUT_DIR.iterdir(), reverse=True):
        if not scan_dir.is_dir():
            continue
        
        if target and target not in scan_dir.name:
            continue
        
        # Gather info about this scan
        info = {
            "name": scan_dir.name,
            "path": str(scan_dir),
            "created": datetime.fromtimestamp(scan_dir.stat().st_mtime).isoformat(),
        }
        
        # Check for key result files
        result_files = {
            "subdomains": scan_dir / "subdomains.txt",
            "webs": scan_dir / "webs.txt",
            "vulnerabilities": scan_dir / "vulnerabilities.txt",
            "osint": scan_dir / "osint.txt",
        }
        
        for key, filepath in result_files.items():
            if filepath.exists():
                lines = filepath.read_text().strip().split("\n")
                info[f"{key}_count"] = len([l for l in lines if l])
        
        results.append(info)
    
    return {
        "results": results,
        "total": len(results)
    }


@mcp_server.tool()
async def get_findings(
    scan_id: int,
    finding_type: str = "all",
    limit: int = 50
) -> Dict[str, Any]:
    """Get findings from a completed or running scan.
    
    Args:
        scan_id: The ID of the scan
        finding_type: Type of findings - "all" (default), "subdomains", 
                      "webs", "vulnerabilities", "emails", "urls"
        limit: Maximum number of findings to return (default: 50)
        
    Returns:
        Dictionary with findings list
    """
    scan = ScanState.get_scan(scan_id)
    if not scan:
        return {"error": f"Scan {scan_id} not found", "scan_id": scan_id}
    
    output_dir = Path(scan["output_dir"]) if scan.get("output_dir") else None
    if not output_dir or not output_dir.exists():
        return {"error": "No output directory found", "scan_id": scan_id}
    
    findings = {
        "scan_id": scan_id,
        "target": scan.get("target"),
        "finding_type": finding_type,
    }
    
    # Map finding types to files
    file_map = {
        "subdomains": ["subdomains.txt", "subs.txt"],
        "webs": ["webs.txt", "alive.txt"],
        "vulnerabilities": ["vulnerabilities.txt", "vulns.txt"],
        "emails": ["emails.txt", "osint/emails.txt"],
        "urls": ["urls.txt", "all_urls.txt"],
    }
    
    if finding_type == "all":
        # Return summary of all finding types
        for ftype, files in file_map.items():
            for filename in files:
                filepath = output_dir / filename
                if filepath.exists():
                    lines = filepath.read_text().strip().split("\n")
                    findings[f"{ftype}_count"] = len([l for l in lines if l])
                    findings[f"{ftype}_preview"] = [l for l in lines if l][:10]
                    break
    else:
        # Return specific finding type
        files = file_map.get(finding_type, [f"{finding_type}.txt"])
        for filename in files:
            filepath = output_dir / filename
            if filepath.exists():
                lines = filepath.read_text().strip().split("\n")
                filtered = [l for l in lines if l]
                findings["total"] = len(filtered)
                findings["findings"] = filtered[:limit]
                findings["truncated"] = len(filtered) > limit
                break
        else:
            findings["error"] = f"No findings of type '{finding_type}' found"
    
    return findings


@mcp_server.tool()
async def stop_scan(scan_id: int) -> Dict[str, Any]:
    """Stop a running reconnaissance scan.
    
    Gracefully stops a running scan. Results collected so far will be saved.
    
    Args:
        scan_id: The ID of the scan to stop
        
    Returns:
        Dictionary with stop operation result
    """
    scan = ScanState.get_scan(scan_id)
    if not scan:
        return {"error": f"Scan {scan_id} not found", "scan_id": scan_id}
    
    process = scan.get("process")
    if not process or scan.get("status") != "running":
        return {
            "scan_id": scan_id,
            "status": scan.get("status"),
            "message": "Scan is not running"
        }
    
    try:
        # Try graceful termination first
        process.terminate()
        
        # Wait briefly for graceful shutdown
        try:
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            # Force kill if needed
            process.kill()
            await process.wait()
        
        ScanState.update_scan(scan_id, status="stopped")
        
        return {
            "scan_id": scan_id,
            "status": "stopped",
            "message": "Scan stopped successfully"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "scan_id": scan_id,
            "status": "error",
            "message": f"Failed to stop scan: {str(e)}"
        }


@mcp_server.tool()
async def get_nuclei_results(scan_id: int, severity: Optional[str] = None) -> Dict[str, Any]:
    """Get Nuclei vulnerability scan results.
    
    Retrieves findings from Nuclei templates run during the scan.
    
    Args:
        scan_id: The ID of the scan
        severity: Filter by severity - "critical", "high", "medium", "low", "info"
        
    Returns:
        Dictionary with Nuclei findings
    """
    scan = ScanState.get_scan(scan_id)
    if not scan:
        return {"error": f"Scan {scan_id} not found", "scan_id": scan_id}
    
    output_dir = Path(scan["output_dir"]) if scan.get("output_dir") else None
    if not output_dir:
        return {"error": "No output directory", "scan_id": scan_id}
    
    # Look for Nuclei output files
    nuclei_files = [
        output_dir / "nuclei.txt",
        output_dir / "vulnerabilities" / "nuclei.txt",
        output_dir / "nuclei_output.txt",
    ]
    
    results = []
    for nuclei_file in nuclei_files:
        if nuclei_file.exists():
            content = nuclei_file.read_text()
            # Parse Nuclei output (simplified)
            for line in content.strip().split("\n"):
                if not line:
                    continue
                
                finding = {"raw": line}
                
                # Try to extract severity from line
                if "[critical]" in line.lower():
                    finding["severity"] = "critical"
                elif "[high]" in line.lower():
                    finding["severity"] = "high"
                elif "[medium]" in line.lower():
                    finding["severity"] = "medium"
                elif "[low]" in line.lower():
                    finding["severity"] = "low"
                else:
                    finding["severity"] = "info"
                
                # Filter by severity if specified
                if severity and finding["severity"] != severity.lower():
                    continue
                
                results.append(finding)
    
    return {
        "scan_id": scan_id,
        "total": len(results),
        "findings": results[:100],  # Limit to 100 results
        "truncated": len(results) > 100
    }
