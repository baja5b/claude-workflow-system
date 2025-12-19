#!/usr/bin/env python3
"""
Scripts MCP Server
Runs local scripts and test commands.
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

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Configuration
ALLOWED_SCRIPT_DIRS = os.getenv("ALLOWED_SCRIPT_DIRS", "").split(",")
MAX_TIMEOUT = int(os.getenv("MAX_SCRIPT_TIMEOUT", "300"))  # 5 minutes default

# Initialize MCP server
server = Server("scripts-mcp")


def is_path_allowed(path: str) -> bool:
    """Check if the path is in an allowed directory."""
    if not ALLOWED_SCRIPT_DIRS or ALLOWED_SCRIPT_DIRS == [""]:
        # If no restrictions, allow all
        return True

    path = Path(path).resolve()
    for allowed_dir in ALLOWED_SCRIPT_DIRS:
        if allowed_dir and path.is_relative_to(Path(allowed_dir).resolve()):
            return True
    return False


async def run_command(
    command: str,
    cwd: Optional[str] = None,
    timeout: int = 60,
    shell: bool = True
) -> dict:
    """Run a command and return the result."""
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=min(timeout, MAX_TIMEOUT)
            )
        except asyncio.TimeoutError:
            process.kill()
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds"
            }

        return {
            "success": process.returncode == 0,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "exit_code": process.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def detect_test_framework(project_path: str) -> Optional[str]:
    """Detect which test framework is used in a project."""
    project_path = Path(project_path)

    # Node.js / JavaScript
    package_json = project_path / "package.json"
    if package_json.exists():
        try:
            pkg = json.loads(package_json.read_text())
            scripts = pkg.get("scripts", {})
            if "test" in scripts:
                return "npm"
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "jest" in deps:
                return "jest"
            if "vitest" in deps:
                return "vitest"
            if "mocha" in deps:
                return "mocha"
        except:
            pass

    # Python
    if (project_path / "pytest.ini").exists() or (project_path / "pyproject.toml").exists():
        return "pytest"
    if (project_path / "setup.py").exists():
        return "python"

    # Rust
    if (project_path / "Cargo.toml").exists():
        return "cargo"

    # Go
    if list(project_path.glob("*_test.go")):
        return "go"

    return None


# Register tools
@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        Tool(
            name="run_script",
            description="Run a script or command",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to run"
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory"
                    },
                    "timeout": {
                        "type": "number",
                        "default": 60,
                        "description": "Timeout in seconds"
                    }
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="run_tests",
            description="Run tests for a project (auto-detects framework)",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project"
                    },
                    "test_pattern": {
                        "type": "string",
                        "description": "Test file pattern or specific test"
                    },
                    "verbose": {
                        "type": "boolean",
                        "default": False,
                        "description": "Verbose output"
                    }
                },
                "required": ["project_path"]
            }
        ),
        Tool(
            name="run_lint",
            description="Run linting for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project"
                    },
                    "fix": {
                        "type": "boolean",
                        "default": False,
                        "description": "Auto-fix issues"
                    }
                },
                "required": ["project_path"]
            }
        ),
        Tool(
            name="run_build",
            description="Run build command for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project"
                    }
                },
                "required": ["project_path"]
            }
        ),
        Tool(
            name="git_status",
            description="Get git status for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project"
                    }
                },
                "required": ["project_path"]
            }
        ),
        Tool(
            name="git_diff",
            description="Get git diff for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project"
                    },
                    "base": {
                        "type": "string",
                        "description": "Base commit/branch (default: HEAD~1)"
                    },
                    "stat_only": {
                        "type": "boolean",
                        "default": False,
                        "description": "Show only file statistics"
                    }
                },
                "required": ["project_path"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""

    if name == "run_script":
        command = arguments["command"]
        cwd = arguments.get("cwd")
        timeout = arguments.get("timeout", 60)

        result = await run_command(command, cwd=cwd, timeout=timeout)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "run_tests":
        project_path = arguments["project_path"]
        test_pattern = arguments.get("test_pattern", "")
        verbose = arguments.get("verbose", False)

        framework = detect_test_framework(project_path)
        if not framework:
            return [TextContent(type="text", text=json.dumps({
                "success": False,
                "error": "Could not detect test framework"
            }, indent=2))]

        commands = {
            "npm": f"npm test {test_pattern}",
            "jest": f"npx jest {'-v' if verbose else ''} {test_pattern}",
            "vitest": f"npx vitest run {test_pattern}",
            "mocha": f"npx mocha {test_pattern}",
            "pytest": f"pytest {'-v' if verbose else ''} {test_pattern}",
            "python": f"python -m unittest {test_pattern}",
            "cargo": f"cargo test {test_pattern}",
            "go": f"go test {'-v' if verbose else ''} ./..."
        }

        command = commands.get(framework, "echo 'Unknown framework'")
        result = await run_command(command, cwd=project_path, timeout=300)
        result["framework"] = framework
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "run_lint":
        project_path = arguments["project_path"]
        fix = arguments.get("fix", False)

        # Try to detect and run appropriate linter
        package_json = Path(project_path) / "package.json"
        if package_json.exists():
            fix_flag = "--fix" if fix else ""
            command = f"npm run lint {fix_flag}"
        elif (Path(project_path) / "pyproject.toml").exists():
            fix_flag = "--fix" if fix else ""
            command = f"ruff check {fix_flag} ."
        else:
            return [TextContent(type="text", text=json.dumps({
                "success": False,
                "error": "Could not detect linter"
            }, indent=2))]

        result = await run_command(command, cwd=project_path, timeout=120)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "run_build":
        project_path = arguments["project_path"]

        package_json = Path(project_path) / "package.json"
        if package_json.exists():
            command = "npm run build"
        elif (Path(project_path) / "Cargo.toml").exists():
            command = "cargo build --release"
        elif (Path(project_path) / "pyproject.toml").exists():
            command = "python -m build"
        else:
            return [TextContent(type="text", text=json.dumps({
                "success": False,
                "error": "Could not detect build system"
            }, indent=2))]

        result = await run_command(command, cwd=project_path, timeout=300)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "git_status":
        project_path = arguments["project_path"]
        result = await run_command("git status --porcelain", cwd=project_path)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "git_diff":
        project_path = arguments["project_path"]
        base = arguments.get("base", "HEAD~1")
        stat_only = arguments.get("stat_only", False)

        stat_flag = "--stat" if stat_only else ""
        command = f"git diff {stat_flag} {base}..HEAD"
        result = await run_command(command, cwd=project_path)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
