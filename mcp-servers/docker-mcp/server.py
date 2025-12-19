#!/usr/bin/env python3
"""
Docker MCP Server
Controls Docker containers on a remote Raspberry Pi via SSH.
"""

import os
import asyncio
import json
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

# SSH imports
try:
    import paramiko
except ImportError:
    print("ERROR: paramiko not installed. Run: pip install paramiko")
    exit(1)

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# SSH Configuration
SSH_HOST = os.getenv("DOCKER_HOST", "raspberry-pi.local")
SSH_PORT = int(os.getenv("DOCKER_SSH_PORT", "22"))
SSH_USER = os.getenv("DOCKER_SSH_USER", "pi")
SSH_KEY_PATH = os.getenv("DOCKER_SSH_KEY", str(Path.home() / ".ssh" / "id_rsa"))

# Initialize MCP server
server = Server("docker-mcp")


class SSHConnection:
    """Manage SSH connection to Docker host."""

    def __init__(self):
        self.client = None

    def connect(self):
        """Establish SSH connection."""
        if self.client and self.client.get_transport() and self.client.get_transport().is_active():
            return self.client

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.client.connect(
                hostname=SSH_HOST,
                port=SSH_PORT,
                username=SSH_USER,
                key_filename=SSH_KEY_PATH,
                timeout=10
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {SSH_HOST}: {e}")

        return self.client

    def execute(self, command: str) -> tuple[str, str, int]:
        """Execute command via SSH and return stdout, stderr, exit_code."""
        client = self.connect()
        stdin, stdout, stderr = client.exec_command(command, timeout=60)
        exit_code = stdout.channel.recv_exit_status()
        return stdout.read().decode(), stderr.read().decode(), exit_code

    def close(self):
        """Close SSH connection."""
        if self.client:
            self.client.close()
            self.client = None


ssh = SSHConnection()


def run_docker_command(command: str) -> dict:
    """Run a Docker command on the remote host."""
    try:
        stdout, stderr, exit_code = ssh.execute(command)
        return {
            "success": exit_code == 0,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# Register tools
@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        Tool(
            name="docker_compose_up",
            description="Start Docker Compose services",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to docker-compose.yml directory"
                    },
                    "service": {
                        "type": "string",
                        "description": "Specific service to start (optional)"
                    },
                    "build": {
                        "type": "boolean",
                        "default": False,
                        "description": "Rebuild images before starting"
                    },
                    "detach": {
                        "type": "boolean",
                        "default": True,
                        "description": "Run in detached mode"
                    }
                },
                "required": ["project_path"]
            }
        ),
        Tool(
            name="docker_compose_down",
            description="Stop Docker Compose services",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to docker-compose.yml directory"
                    },
                    "volumes": {
                        "type": "boolean",
                        "default": False,
                        "description": "Remove volumes"
                    }
                },
                "required": ["project_path"]
            }
        ),
        Tool(
            name="docker_logs",
            description="Get container logs",
            inputSchema={
                "type": "object",
                "properties": {
                    "container": {
                        "type": "string",
                        "description": "Container name or ID"
                    },
                    "lines": {
                        "type": "number",
                        "default": 100,
                        "description": "Number of lines to retrieve"
                    },
                    "follow": {
                        "type": "boolean",
                        "default": False,
                        "description": "Follow log output (streams)"
                    }
                },
                "required": ["container"]
            }
        ),
        Tool(
            name="docker_ps",
            description="List running containers",
            inputSchema={
                "type": "object",
                "properties": {
                    "all": {
                        "type": "boolean",
                        "default": False,
                        "description": "Show all containers (including stopped)"
                    }
                }
            }
        ),
        Tool(
            name="docker_exec",
            description="Execute command in a running container",
            inputSchema={
                "type": "object",
                "properties": {
                    "container": {
                        "type": "string",
                        "description": "Container name or ID"
                    },
                    "command": {
                        "type": "string",
                        "description": "Command to execute"
                    }
                },
                "required": ["container", "command"]
            }
        ),
        Tool(
            name="docker_stats",
            description="Get container resource usage statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "container": {
                        "type": "string",
                        "description": "Container name or ID (optional, all if not specified)"
                    }
                }
            }
        ),
        Tool(
            name="docker_restart",
            description="Restart a container",
            inputSchema={
                "type": "object",
                "properties": {
                    "container": {
                        "type": "string",
                        "description": "Container name or ID"
                    }
                },
                "required": ["container"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""

    if name == "docker_compose_up":
        path = arguments["project_path"]
        service = arguments.get("service", "")
        build = "--build" if arguments.get("build", False) else ""
        detach = "-d" if arguments.get("detach", True) else ""
        cmd = f"cd {path} && docker-compose up {build} {detach} {service}".strip()
        result = run_docker_command(cmd)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "docker_compose_down":
        path = arguments["project_path"]
        volumes = "-v" if arguments.get("volumes", False) else ""
        cmd = f"cd {path} && docker-compose down {volumes}".strip()
        result = run_docker_command(cmd)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "docker_logs":
        container = arguments["container"]
        lines = arguments.get("lines", 100)
        cmd = f"docker logs --tail {lines} {container}"
        result = run_docker_command(cmd)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "docker_ps":
        all_flag = "-a" if arguments.get("all", False) else ""
        cmd = f"docker ps {all_flag} --format 'table {{{{.Names}}}}\\t{{{{.Status}}}}\\t{{{{.Ports}}}}'".strip()
        result = run_docker_command(cmd)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "docker_exec":
        container = arguments["container"]
        command = arguments["command"]
        cmd = f"docker exec {container} {command}"
        result = run_docker_command(cmd)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "docker_stats":
        container = arguments.get("container", "")
        cmd = f"docker stats --no-stream --format 'table {{{{.Name}}}}\\t{{{{.CPUPerc}}}}\\t{{{{.MemUsage}}}}' {container}".strip()
        result = run_docker_command(cmd)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "docker_restart":
        container = arguments["container"]
        cmd = f"docker restart {container}"
        result = run_docker_command(cmd)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
