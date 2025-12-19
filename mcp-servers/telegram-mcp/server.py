#!/usr/bin/env python3
"""
Telegram MCP Server
Sends notifications to Telegram for workflow events.
"""

import os
import asyncio
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    from mcp.server.stdio import stdio_server
except ImportError:
    print("ERROR: MCP SDK not installed. Run: pip install mcp")
    exit(1)

# Telegram imports
try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    exit(1)

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Initialize MCP server
server = Server("telegram-mcp")


def get_telegram_api_url(method: str) -> str:
    """Get Telegram API URL for a method."""
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"


async def send_telegram_message(
    message: str,
    parse_mode: str = "Markdown",
    disable_notification: bool = False
) -> dict:
    """Send a message via Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return {"error": "Telegram credentials not configured"}

    url = get_telegram_api_url("sendMessage")
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": parse_mode,
        "disable_notification": disable_notification
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        return response.json()


async def send_telegram_document(
    file_path: str,
    caption: Optional[str] = None
) -> dict:
    """Send a file via Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return {"error": "Telegram credentials not configured"}

    url = get_telegram_api_url("sendDocument")

    async with httpx.AsyncClient() as client:
        with open(file_path, "rb") as f:
            files = {"document": f}
            data = {"chat_id": TELEGRAM_CHAT_ID}
            if caption:
                data["caption"] = caption
            response = await client.post(url, data=data, files=files)
            return response.json()


# Register tools
@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        Tool(
            name="telegram_send",
            description="Send a message to Telegram",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to send"
                    },
                    "parse_mode": {
                        "type": "string",
                        "enum": ["Markdown", "HTML", "MarkdownV2"],
                        "default": "Markdown",
                        "description": "Message formatting mode"
                    },
                    "silent": {
                        "type": "boolean",
                        "default": False,
                        "description": "Send without notification sound"
                    }
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="telegram_send_file",
            description="Send a file to Telegram",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to send"
                    },
                    "caption": {
                        "type": "string",
                        "description": "Optional caption for the file"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="telegram_workflow_start",
            description="Send workflow start notification",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "Workflow ID (e.g., WF-2025-001)"
                    },
                    "project": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "title": {
                        "type": "string",
                        "description": "Workflow title"
                    }
                },
                "required": ["workflow_id", "project", "title"]
            }
        ),
        Tool(
            name="telegram_workflow_complete",
            description="Send workflow completion notification",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "Workflow ID"
                    },
                    "project": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "title": {
                        "type": "string",
                        "description": "Workflow title"
                    },
                    "duration_minutes": {
                        "type": "number",
                        "description": "Duration in minutes"
                    },
                    "tests_passed": {
                        "type": "number",
                        "description": "Number of tests passed"
                    },
                    "tests_total": {
                        "type": "number",
                        "description": "Total number of tests"
                    }
                },
                "required": ["workflow_id", "project", "title"]
            }
        ),
        Tool(
            name="telegram_workflow_error",
            description="Send workflow error notification",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "Workflow ID"
                    },
                    "project": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "title": {
                        "type": "string",
                        "description": "Workflow title"
                    },
                    "phase": {
                        "type": "string",
                        "description": "Phase where error occurred"
                    },
                    "error": {
                        "type": "string",
                        "description": "Error message"
                    }
                },
                "required": ["workflow_id", "project", "title", "error"]
            }
        ),
        Tool(
            name="telegram_workflow_decision",
            description="Send decision required notification",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "Workflow ID"
                    },
                    "title": {
                        "type": "string",
                        "description": "Workflow title"
                    },
                    "question": {
                        "type": "string",
                        "description": "The decision/question"
                    }
                },
                "required": ["workflow_id", "title", "question"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""

    if name == "telegram_send":
        result = await send_telegram_message(
            message=arguments["message"],
            parse_mode=arguments.get("parse_mode", "Markdown"),
            disable_notification=arguments.get("silent", False)
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "telegram_send_file":
        result = await send_telegram_document(
            file_path=arguments["file_path"],
            caption=arguments.get("caption")
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "telegram_workflow_start":
        message = f"""🚀 *Workflow gestartet*

*Projekt:* {arguments['project']}
*Task:* {arguments['title']}
*ID:* `{arguments['workflow_id']}`
*Status:* Planning"""
        result = await send_telegram_message(message)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "telegram_workflow_complete":
        duration = arguments.get('duration_minutes', '?')
        tests = f"{arguments.get('tests_passed', '?')}/{arguments.get('tests_total', '?')}"
        message = f"""✅ *Workflow abgeschlossen*

*Projekt:* {arguments['project']}
*Task:* {arguments['title']}
*ID:* `{arguments['workflow_id']}`
*Dauer:* {duration} min
*Tests:* {tests} passed"""
        result = await send_telegram_message(message)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "telegram_workflow_error":
        phase = arguments.get('phase', 'Unknown')
        message = f"""❌ *Fehler aufgetreten*

*Projekt:* {arguments['project']}
*Task:* {arguments['title']}
*ID:* `{arguments['workflow_id']}`
*Phase:* {phase}
*Error:* `{arguments['error']}`"""
        result = await send_telegram_message(message)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "telegram_workflow_decision":
        message = f"""❓ *Entscheidung erforderlich*

*Workflow:* {arguments['title']}
*ID:* `{arguments['workflow_id']}`
*Frage:* {arguments['question']}

→ Öffne Claude Code zum Antworten"""
        result = await send_telegram_message(message)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
