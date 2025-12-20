#!/usr/bin/env python3
"""
Workflow MCP Server
Manages workflows via the Pi API.
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

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    exit(1)

from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Configuration
API_BASE_URL = os.getenv("WORKFLOW_API_URL", "http://MCP-Server.local:8100")

# Initialize MCP server
server = Server("workflow-mcp")


async def api_request(method: str, endpoint: str, data: dict = None) -> dict:
    """Make request to Workflow API."""
    url = f"{API_BASE_URL}{endpoint}"
    async with httpx.AsyncClient(timeout=30) as client:
        if method == "GET":
            response = await client.get(url)
        elif method == "POST":
            response = await client.post(url, json=data)
        elif method == "PATCH":
            response = await client.patch(url, json=data)
        else:
            return {"error": f"Unknown method: {method}"}

        if response.status_code >= 400:
            return {"error": response.text, "status_code": response.status_code}
        return response.json()


@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        Tool(
            name="workflow_create",
            description="Create a new workflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project name"},
                    "project_path": {"type": "string", "description": "Full project path"},
                    "title": {"type": "string", "description": "Workflow title"},
                    "requirements": {"type": "string", "description": "JSON requirements"}
                },
                "required": ["project", "title"]
            }
        ),
        Tool(
            name="workflow_get",
            description="Get a workflow by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string", "description": "Workflow ID (e.g., WF-2025-001)"}
                },
                "required": ["workflow_id"]
            }
        ),
        Tool(
            name="workflow_list",
            description="List workflows",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status"},
                    "project": {"type": "string", "description": "Filter by project"}
                }
            }
        ),
        Tool(
            name="workflow_list_active",
            description="List all active workflows",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="workflow_update",
            description="Update a workflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string", "description": "Workflow ID"},
                    "status": {"type": "string", "description": "New status"},
                    "plan": {"type": "string", "description": "JSON plan"},
                    "requirements": {"type": "string", "description": "JSON requirements"},
                    "github_issue_number": {"type": "integer", "description": "Linked GitHub issue"}
                },
                "required": ["workflow_id"]
            }
        ),
        Tool(
            name="workflow_add_task",
            description="Add a task to a workflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string", "description": "Workflow ID"},
                    "sequence": {"type": "integer", "description": "Task sequence number"},
                    "description": {"type": "string", "description": "Task description"}
                },
                "required": ["workflow_id", "sequence", "description"]
            }
        ),
        Tool(
            name="workflow_update_task",
            description="Update a task status",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "Task ID"},
                    "status": {"type": "string", "description": "New status: PENDING, IN_PROGRESS, COMPLETED, FAILED, SKIPPED"},
                    "result": {"type": "string", "description": "Task result"},
                    "error_message": {"type": "string", "description": "Error message if failed"}
                },
                "required": ["task_id", "status"]
            }
        ),
        Tool(
            name="workflow_get_tasks",
            description="Get all tasks for a workflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string", "description": "Workflow ID"}
                },
                "required": ["workflow_id"]
            }
        ),
        Tool(
            name="workflow_add_test_result",
            description="Record a test result",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string", "description": "Workflow ID"},
                    "test_type": {"type": "string", "description": "Type: unit, integration, e2e, review"},
                    "test_name": {"type": "string", "description": "Test name"},
                    "passed": {"type": "boolean", "description": "Pass/fail"},
                    "output": {"type": "string", "description": "Test output"}
                },
                "required": ["workflow_id", "test_type", "test_name", "passed"]
            }
        ),
        Tool(
            name="workflow_stats",
            description="Get workflow statistics",
            inputSchema={"type": "object", "properties": {}}
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""

    if name == "workflow_create":
        result = await api_request("POST", "/workflows", {
            "project": arguments["project"],
            "project_path": arguments.get("project_path"),
            "title": arguments["title"],
            "requirements": arguments.get("requirements")
        })
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "workflow_get":
        result = await api_request("GET", f"/workflows/{arguments['workflow_id']}")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "workflow_list":
        params = []
        if arguments.get("status"):
            params.append(f"status={arguments['status']}")
        if arguments.get("project"):
            params.append(f"project={arguments['project']}")
        query = "?" + "&".join(params) if params else ""
        result = await api_request("GET", f"/workflows{query}")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "workflow_list_active":
        result = await api_request("GET", "/workflows/active")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "workflow_update":
        update_data = {}
        if arguments.get("status"):
            update_data["status"] = arguments["status"]
        if arguments.get("plan"):
            update_data["plan"] = arguments["plan"]
        if arguments.get("requirements"):
            update_data["requirements"] = arguments["requirements"]
        if arguments.get("github_issue_number"):
            update_data["github_issue_number"] = arguments["github_issue_number"]

        result = await api_request("PATCH", f"/workflows/{arguments['workflow_id']}", update_data)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "workflow_add_task":
        result = await api_request("POST", f"/workflows/{arguments['workflow_id']}/tasks", {
            "workflow_id": arguments["workflow_id"],
            "sequence": arguments["sequence"],
            "description": arguments["description"]
        })
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "workflow_update_task":
        update_data = {"status": arguments["status"]}
        if arguments.get("result"):
            update_data["result"] = arguments["result"]
        if arguments.get("error_message"):
            update_data["error_message"] = arguments["error_message"]

        result = await api_request("PATCH", f"/tasks/{arguments['task_id']}", update_data)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "workflow_get_tasks":
        result = await api_request("GET", f"/workflows/{arguments['workflow_id']}/tasks")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "workflow_add_test_result":
        result = await api_request("POST", "/test-results", {
            "workflow_id": arguments["workflow_id"],
            "test_type": arguments["test_type"],
            "test_name": arguments["test_name"],
            "passed": arguments["passed"],
            "output": arguments.get("output")
        })
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "workflow_stats":
        result = await api_request("GET", "/stats")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
