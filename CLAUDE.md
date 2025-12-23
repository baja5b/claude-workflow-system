# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-gesteuertes Entwicklungs-Workflow-System für Claude Code. Provides structured development workflows with requirements planning, confirmation gates, task queues, 4-Augen-Prinzip (independent test review), and mobile notifications via Telegram.

## Architecture

```
┌─────────────────────┐         ┌─────────────────────┐
│  Windows PC         │   HTTP  │  Raspberry Pi       │
│  (Claude Code)      │ ──────► │  (Docker Host)      │
│                     │         │                     │
│  MCP Servers:       │         │  FastAPI Server     │
│  - workflow-mcp ────┼─────────┼► :8100              │
│  - telegram-mcp     │         │  SQLite Database    │
│  - test-runner-mcp  │         │                     │
│  - docker-mcp       │         │                     │
│  - scripts-mcp      │         │                     │
└─────────────────────┘         └─────────────────────┘
```

**Workflow State Machine:**
```
PLANNING → CONFIRMED → EXECUTING → TESTING → DOCUMENTING → COMPLETED
    ↓         ↓           ↓          ↓           ↓
 REJECTED   FAILED      FAILED     FAILED      FAILED
```

## Key Components

### MCP Servers (`mcp-servers/`)
- **workflow-mcp**: Core workflow management via API (create, update, tasks, test results)
- **telegram-mcp**: Mobile notifications for workflow events
- **test-runner-mcp**: Remote testing on dev/prod servers via SSH
- **docker-mcp**: Container management on Raspberry Pi
- **scripts-mcp**: Local automation scripts

### API Server (`api/server.py`)
FastAPI server running on Raspberry Pi. Uses SQLite database defined in `schemas/workflows.sql`.

### Workflow Commands (`commands/workflow/`)
Claude Code custom commands (slash commands):
- `/workflow:start <title>` - Start new workflow, creates GitHub issue
- `/workflow:confirm` - Approve plan and start execution
- `/workflow:execute` - Execute pending tasks
- `/workflow:test` - Run 4-Augen test (independent review)
- `/workflow:status` - Show current workflow status
- `/workflow:document` - Generate documentation
- `/workflow:cleanup` - Remove deprecated code

## Common Commands

```bash
# Run API tests
pytest tests/test_api.py -v

# Test individual MCP server
cd mcp-servers/telegram-mcp
pip install -r requirements.txt
python server.py

# Run all MCP server tests
pytest mcp-servers/*/tests/

# Install system (Windows PowerShell as Admin)
.\install.ps1

# Force reinstall
.\install.ps1 -Force
```

## Development Patterns

### Workflow Lifecycle
1. `/workflow:start` creates workflow with status PLANNING
2. User reviews plan, provides feedback
3. `/workflow:confirm` transitions to CONFIRMED → EXECUTING
4. Tasks execute sequentially, each tracked via `workflow_update_task`
5. `/workflow:test` runs 4-Augen review (code review agent + automated tests)
6. On success → COMPLETED, failure → FAILED with Telegram notification

### MCP Server Pattern
All MCP servers follow the same structure:
```python
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

server = Server("server-name")

@server.list_tools()
async def list_tools():
    return [Tool(...)]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    # Handle tool calls
    return [TextContent(type="text", text=json.dumps(result))]
```

### Workflow MCP Tools
- `workflow_create`, `workflow_get`, `workflow_list`, `workflow_list_active`
- `workflow_update`, `workflow_add_task`, `workflow_update_task`, `workflow_get_tasks`
- `workflow_add_test_result`, `workflow_stats`

### Database Schema
Main tables: `workflows`, `tasks`, `notifications`, `test_results`
Views: `active_workflows`, `workflow_summary`

## Configuration

### Environment Variables
- `WORKFLOW_API_URL` - API base URL (default: `http://MCP-Server.local:8100`)
- `WORKFLOW_DB_PATH` - SQLite database path (default: `/opt/workflow-system/workflows.db`)
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` - Telegram bot credentials
- `DEV_SERVER`, `PROD_SERVER` - Server IPs for test-runner
- `SSH_KEY`, `SSH_USER` - SSH credentials for remote testing

### Installation Paths
- Commands: `~/.claude/commands/workflow/`
- MCP Servers: `~/.claude/mcp-servers/`
- Settings: `~/.claude/settings.json`
- Database: `~/.claude/workflow-data/workflows.db`

## Language

The codebase and documentation are written in German. Workflow commands output German text.
