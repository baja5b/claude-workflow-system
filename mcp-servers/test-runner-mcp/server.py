#!/usr/bin/env python3
"""
Test Runner MCP Server
Runs tests on remote servers (dev/prod) and reports results.
"""

import os
import asyncio
import json
import subprocess
from pathlib import Path
from typing import Optional

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    from mcp.server.stdio import stdio_server
except ImportError:
    print("ERROR: MCP SDK not installed. Run: pip install mcp")
    exit(1)

from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Configuration
DEV_SERVER = os.getenv("DEV_SERVER", "188.245.154.83")
PROD_SERVER = os.getenv("PROD_SERVER", "91.98.30.67")
SSH_KEY = os.getenv("SSH_KEY", "~/.ssh/hetzner_musictrackers")
SSH_USER = os.getenv("SSH_USER", "root")
DEV_URL = os.getenv("DEV_URL", "https://dev.musictrackers.app")
PROD_URL = os.getenv("PROD_URL", "https://musictrackers.app")

# Initialize MCP server
server = Server("test-runner-mcp")


async def run_ssh_command(server_ip: str, command: str) -> dict:
    """Run a command on remote server via SSH."""
    ssh_key_path = os.path.expanduser(SSH_KEY)
    ssh_cmd = [
        "ssh",
        "-i", ssh_key_path,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        f"{SSH_USER}@{server_ip}",
        command
    ]

    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out after 5 minutes",
            "exit_code": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1
        }


async def run_local_command(command: str, cwd: str = None) -> dict:
    """Run a local command."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            cwd=cwd
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out after 10 minutes",
            "exit_code": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1
        }


@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        Tool(
            name="test_health_check",
            description="Check if a server is healthy (API responds)",
            inputSchema={
                "type": "object",
                "properties": {
                    "environment": {
                        "type": "string",
                        "enum": ["dev", "prod"],
                        "description": "Which environment to check"
                    }
                },
                "required": ["environment"]
            }
        ),
        Tool(
            name="test_api_endpoint",
            description="Test a specific API endpoint",
            inputSchema={
                "type": "object",
                "properties": {
                    "environment": {
                        "type": "string",
                        "enum": ["dev", "prod"],
                        "description": "Which environment"
                    },
                    "endpoint": {
                        "type": "string",
                        "description": "API endpoint path (e.g., /api/public/auto-playlists)"
                    },
                    "expected_status": {
                        "type": "integer",
                        "description": "Expected HTTP status code (default 200)"
                    }
                },
                "required": ["environment", "endpoint"]
            }
        ),
        Tool(
            name="test_run_smoke_tests",
            description="Run smoke tests against dev or prod server",
            inputSchema={
                "type": "object",
                "properties": {
                    "environment": {
                        "type": "string",
                        "enum": ["dev", "prod"],
                        "description": "Which environment"
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Path to MusicTracker project (for running Playwright)"
                    }
                },
                "required": ["environment", "project_path"]
            }
        ),
        Tool(
            name="test_run_unit_tests",
            description="Run unit tests locally",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project"
                    },
                    "test_type": {
                        "type": "string",
                        "enum": ["frontend", "backend", "both"],
                        "description": "Which tests to run"
                    }
                },
                "required": ["project_path", "test_type"]
            }
        ),
        Tool(
            name="test_check_deployment",
            description="Verify deployment was successful by checking commit hash",
            inputSchema={
                "type": "object",
                "properties": {
                    "environment": {
                        "type": "string",
                        "enum": ["dev", "prod"],
                        "description": "Which environment"
                    },
                    "expected_commit": {
                        "type": "string",
                        "description": "Expected git commit hash (short or full)"
                    }
                },
                "required": ["environment"]
            }
        ),
        Tool(
            name="test_check_containers",
            description="Check if all Docker containers are running and healthy",
            inputSchema={
                "type": "object",
                "properties": {
                    "environment": {
                        "type": "string",
                        "enum": ["dev", "prod"],
                        "description": "Which environment"
                    }
                },
                "required": ["environment"]
            }
        ),
        Tool(
            name="test_run_lint",
            description="Run linting checks locally",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project"
                    },
                    "lint_type": {
                        "type": "string",
                        "enum": ["frontend", "backend", "both"],
                        "description": "Which linting to run"
                    }
                },
                "required": ["project_path", "lint_type"]
            }
        ),
        Tool(
            name="test_comprehensive",
            description="Run a comprehensive test suite: health, containers, API, and optionally smoke tests",
            inputSchema={
                "type": "object",
                "properties": {
                    "environment": {
                        "type": "string",
                        "enum": ["dev", "prod"],
                        "description": "Which environment"
                    },
                    "include_smoke_tests": {
                        "type": "boolean",
                        "description": "Whether to run Playwright smoke tests (slower)"
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Path to project (required if include_smoke_tests is true)"
                    }
                },
                "required": ["environment"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""

    if name == "test_health_check":
        env = arguments["environment"]
        url = DEV_URL if env == "dev" else PROD_URL
        server_ip = DEV_SERVER if env == "dev" else PROD_SERVER

        # Check API health
        result = await run_ssh_command(server_ip, f"curl -s -o /dev/null -w '%{{http_code}}' {url}/api/health")

        status = {
            "environment": env,
            "url": url,
            "health_check": result["success"] and result["stdout"].strip() == "200",
            "http_status": result["stdout"].strip() if result["success"] else "ERROR",
            "error": result["stderr"] if not result["success"] else None
        }

        return [TextContent(type="text", text=json.dumps(status, indent=2))]

    elif name == "test_api_endpoint":
        env = arguments["environment"]
        endpoint = arguments["endpoint"]
        expected_status = arguments.get("expected_status", 200)
        url = DEV_URL if env == "dev" else PROD_URL
        server_ip = DEV_SERVER if env == "dev" else PROD_SERVER

        full_url = f"{url}{endpoint}"
        result = await run_ssh_command(
            server_ip,
            f"curl -s -o /tmp/response.json -w '%{{http_code}}' '{full_url}' && cat /tmp/response.json | head -500"
        )

        # Parse response
        lines = result["stdout"].strip().split("\n")
        http_code = lines[0] if lines else "000"
        response_body = "\n".join(lines[1:]) if len(lines) > 1 else ""

        status = {
            "environment": env,
            "endpoint": endpoint,
            "url": full_url,
            "http_status": http_code,
            "expected_status": expected_status,
            "passed": http_code == str(expected_status),
            "response_preview": response_body[:500] if response_body else None,
            "error": result["stderr"] if not result["success"] else None
        }

        return [TextContent(type="text", text=json.dumps(status, indent=2))]

    elif name == "test_run_smoke_tests":
        env = arguments["environment"]
        project_path = arguments["project_path"]
        base_url = DEV_URL if env == "dev" else PROD_URL

        # Run Playwright smoke tests
        cmd = f"cd {project_path} && npm run test:smoke -- --base-url={base_url}"
        result = await run_local_command(cmd)

        status = {
            "environment": env,
            "test_type": "smoke",
            "passed": result["success"],
            "output": result["stdout"][-2000:] if result["stdout"] else "",
            "errors": result["stderr"][-1000:] if result["stderr"] else None
        }

        return [TextContent(type="text", text=json.dumps(status, indent=2))]

    elif name == "test_run_unit_tests":
        project_path = arguments["project_path"]
        test_type = arguments["test_type"]

        results = {}

        if test_type in ["frontend", "both"]:
            cmd = f"cd {project_path}/frontend && npm test -- --passWithNoTests"
            result = await run_local_command(cmd)
            results["frontend"] = {
                "passed": result["success"],
                "output": result["stdout"][-1500:] if result["stdout"] else "",
                "errors": result["stderr"][-500:] if result["stderr"] else None
            }

        if test_type in ["backend", "both"]:
            cmd = f"cd {project_path}/backend && pytest -v --tb=short"
            result = await run_local_command(cmd)
            results["backend"] = {
                "passed": result["success"],
                "output": result["stdout"][-1500:] if result["stdout"] else "",
                "errors": result["stderr"][-500:] if result["stderr"] else None
            }

        return [TextContent(type="text", text=json.dumps(results, indent=2))]

    elif name == "test_check_deployment":
        env = arguments["environment"]
        expected_commit = arguments.get("expected_commit")
        server_ip = DEV_SERVER if env == "dev" else PROD_SERVER

        # Get deployed commit
        result = await run_ssh_command(
            server_ip,
            "cd /opt/musictracker/current && git log -1 --oneline"
        )

        deployed_commit = result["stdout"].strip().split()[0] if result["success"] else "UNKNOWN"

        status = {
            "environment": env,
            "deployed_commit": deployed_commit,
            "expected_commit": expected_commit,
            "matches": expected_commit is None or deployed_commit.startswith(expected_commit) or expected_commit.startswith(deployed_commit),
            "full_output": result["stdout"].strip()
        }

        return [TextContent(type="text", text=json.dumps(status, indent=2))]

    elif name == "test_check_containers":
        env = arguments["environment"]
        server_ip = DEV_SERVER if env == "dev" else PROD_SERVER

        result = await run_ssh_command(
            server_ip,
            "docker ps --format '{{.Names}}|{{.Status}}|{{.Ports}}' 2>/dev/null"
        )

        containers = []
        if result["success"]:
            for line in result["stdout"].strip().split("\n"):
                if line and "|" in line:
                    parts = line.split("|")
                    containers.append({
                        "name": parts[0],
                        "status": parts[1] if len(parts) > 1 else "unknown",
                        "healthy": "Up" in parts[1] if len(parts) > 1 else False
                    })

        all_healthy = all(c["healthy"] for c in containers) if containers else False

        status = {
            "environment": env,
            "containers": containers,
            "total": len(containers),
            "all_healthy": all_healthy,
            "error": result["stderr"] if not result["success"] else None
        }

        return [TextContent(type="text", text=json.dumps(status, indent=2))]

    elif name == "test_run_lint":
        project_path = arguments["project_path"]
        lint_type = arguments["lint_type"]

        results = {}

        if lint_type in ["frontend", "both"]:
            cmd = f"cd {project_path}/frontend && npm run lint"
            result = await run_local_command(cmd)
            results["frontend"] = {
                "passed": result["success"],
                "output": result["stdout"][-1000:] if result["stdout"] else "",
                "errors": result["stderr"][-500:] if result["stderr"] else None
            }

        if lint_type in ["backend", "both"]:
            cmd = f"cd {project_path}/backend && ruff check ."
            result = await run_local_command(cmd)
            results["backend"] = {
                "passed": result["success"],
                "output": result["stdout"][-1000:] if result["stdout"] else "",
                "errors": result["stderr"][-500:] if result["stderr"] else None
            }

        return [TextContent(type="text", text=json.dumps(results, indent=2))]

    elif name == "test_comprehensive":
        env = arguments["environment"]
        include_smoke = arguments.get("include_smoke_tests", False)
        project_path = arguments.get("project_path")
        url = DEV_URL if env == "dev" else PROD_URL
        server_ip = DEV_SERVER if env == "dev" else PROD_SERVER

        results = {
            "environment": env,
            "tests": {}
        }

        # 1. Health Check
        health_result = await run_ssh_command(
            server_ip,
            f"curl -s -o /dev/null -w '%{{http_code}}' {url}/api/health"
        )
        results["tests"]["health"] = {
            "passed": health_result["success"] and health_result["stdout"].strip() == "200",
            "http_status": health_result["stdout"].strip()
        }

        # 2. Container Check
        container_result = await run_ssh_command(
            server_ip,
            "docker ps --format '{{.Names}}:{{.Status}}' | grep -E 'mt_|musictrackers_'"
        )
        containers_up = container_result["stdout"].count("Up") if container_result["success"] else 0
        results["tests"]["containers"] = {
            "passed": containers_up >= 4,  # At least api, nginx, db, redis
            "containers_up": containers_up
        }

        # 3. API Endpoints
        critical_endpoints = [
            "/api/health",
            "/api/public/auto-playlists",
            "/api/public/stats"
        ]

        endpoint_results = []
        for endpoint in critical_endpoints:
            ep_result = await run_ssh_command(
                server_ip,
                f"curl -s -o /dev/null -w '%{{http_code}}' '{url}{endpoint}'"
            )
            passed = ep_result["success"] and ep_result["stdout"].strip() in ["200", "201"]
            endpoint_results.append({
                "endpoint": endpoint,
                "passed": passed,
                "status": ep_result["stdout"].strip()
            })

        results["tests"]["api_endpoints"] = {
            "passed": all(r["passed"] for r in endpoint_results),
            "details": endpoint_results
        }

        # 4. Optional Smoke Tests
        if include_smoke and project_path:
            cmd = f"cd {project_path} && npm run test:smoke -- --base-url={url}"
            smoke_result = await run_local_command(cmd)
            results["tests"]["smoke"] = {
                "passed": smoke_result["success"],
                "output_tail": smoke_result["stdout"][-500:] if smoke_result["stdout"] else ""
            }

        # Overall status
        all_passed = all(
            test["passed"]
            for test in results["tests"].values()
        )
        results["overall_passed"] = all_passed
        results["summary"] = "ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED"

        return [TextContent(type="text", text=json.dumps(results, indent=2))]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
