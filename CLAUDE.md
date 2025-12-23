# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-gesteuertes Entwicklungs-Workflow-System für Claude Code. Jira Cloud ist das Master-System für Workflows mit automatischer Synchronisation zu GitHub. Bietet strukturierte Entwicklungs-Workflows mit Requirements Planning, Confirmation Gates, automatischer Task-Verarbeitung, 4-Augen-Prinzip (Independent Review), und Mobile Notifications via Telegram.

## Architecture

```
┌─────────────────────┐         ┌─────────────────────┐
│  Windows PC         │   API   │  Jira Cloud         │
│  (Claude Code)      │ ──────► │  (Master-System)    │
│                     │         │                     │
│  MCP Servers:       │         │  9 Status-Spalten:  │
│  - jira-mcp ────────┼─────────┼► TO DO              │
│  - telegram-mcp     │         │  PLANNED            │
│  - workflow-mcp     │         │  PLANNED AND        │
│  - test-runner-mcp  │         │   CONFIRMED         │
│  - docker-mcp       │         │  IN PROGRESS        │
│  - scripts-mcp      │         │  REVIEW             │
│                     │         │  TESTING            │
│  GitHub Sync:       │         │  MANUAL TESTING     │
│  - Issues ──────────┼─────────┼► DOCUMENTATION      │
│  - Branches         │         │  DONE               │
│  - Pull Requests    │         │                     │
└─────────────────────┘         └─────────────────────┘
```

**Jira Workflow State Machine:**
```
TO DO → PLANNED → PLANNED AND CONFIRMED → IN PROGRESS → REVIEW → TESTING → MANUAL TESTING → DOCUMENTATION → DONE
```

**GitHub Sync:**
- Jira TO DO → GitHub Issue erstellt
- PLANNED AND CONFIRMED → Branch erstellt (feature/{KEY}-{title})
- REVIEW → Draft PR erstellt
- DONE ← PR merged

## Key Components

### MCP Servers (`mcp-servers/`)
- **jira-mcp**: Jira Cloud Integration (Issues, Transitions, Comments, Worker, GitHub-Sync)
- **telegram-mcp**: Mobile notifications mit Jira-Links
- **workflow-mcp**: Legacy workflow management (optional)
- **test-runner-mcp**: Remote testing on dev/prod servers via SSH
- **docker-mcp**: Container management on Raspberry Pi
- **scripts-mcp**: Local automation scripts

### Jira MCP Server (`mcp-servers/jira-mcp/`)
```
jira-mcp/
├── server.py           # MCP Server mit allen Tools
├── jira_client.py      # Jira REST API Client
├── worker.py           # Polling-Worker (verarbeitet Issues)
├── github_sync.py      # GitHub CLI Integration
├── handlers/           # Handler pro Status
│   ├── todo_handler.py
│   ├── planned_handler.py
│   ├── confirmed_handler.py
│   ├── progress_handler.py
│   ├── review_handler.py
│   ├── testing_handler.py
│   └── documentation_handler.py
├── requirements.txt
└── .env.example
```

### Workflow Commands (`commands/workflow/`)
Claude Code custom commands (slash commands):
- `/workflow:start <title>` - Neues Jira Issue erstellen, Plan generieren
- `/workflow:confirm [KEY]` - Plan bestätigen → PLANNED AND CONFIRMED
- `/workflow:start-working` - Worker starten, Issues automatisch verarbeiten
- `/workflow:test [KEY]` - 4-Augen Test ausführen
- `/workflow:status [KEY]` - Jira-Status anzeigen
- `/workflow:document [KEY]` - Dokumentation generieren → DONE

## Common Commands

```bash
# Install system (Windows PowerShell as Admin)
.\install.ps1

# Force reinstall
.\install.ps1 -Force

# Test Jira MCP server
cd mcp-servers/jira-mcp
pip install -r requirements.txt
python server.py

# Test GitHub sync
python github_sync.py status <pr_number>
```

## Jira MCP Tools

### Issue Operations
- `jira_get_issue` - Issue abrufen
- `jira_list_issues` - JQL-Suche
- `jira_list_by_status` - Issues nach Status
- `jira_create_issue` - Neues Issue erstellen
- `jira_add_comment` - Kommentar hinzufügen
- `jira_get_comments` - Kommentare abrufen
- `jira_transition` - Status ändern
- `jira_update_issue` - Issue aktualisieren

### Worker Operations
- `jira_poll_once` - Einmal alle Issues verarbeiten
- `jira_process_issue` - Einzelnes Issue verarbeiten
- `jira_get_workable` - Alle bearbeitbaren Issues abrufen

### GitHub Sync
- `github_create_issue` - GitHub Issue erstellen
- `github_create_branch` - Feature-Branch erstellen
- `github_create_pr` - Pull Request erstellen
- `github_pr_status` - PR-Status abrufen
- `github_merge_pr` - PR mergen
- `github_find_by_jira` - GitHub Issue/PR nach Jira-Key suchen

## Status Automation

| Jira Status | Automatische Aktion |
|-------------|---------------------|
| TO DO | Plan erstellen → PLANNED |
| PLANNED | Warten auf User-Feedback (Kommentare prüfen) |
| PLANNED AND CONFIRMED | Arbeit starten → IN PROGRESS |
| IN PROGRESS | Implementierung, bei Blockern: Telegram |
| REVIEW | Code-Review → TESTING |
| TESTING | Tests ausführen → MANUAL TESTING |
| MANUAL TESTING | User testet manuell |
| DOCUMENTATION | Doku erstellen → DONE |

## Configuration

### Per-Repository Configuration (`.claude-workflow.json`)

Lege eine `.claude-workflow.json` im Repo-Root an, um projekt-spezifische Einstellungen zu definieren:

```json
{
  "jira": {
    "project_key": "YOUR_PROJECT_KEY",
    "default_issue_type": "Task"
  },
  "github": {
    "base_branch": "main"
  },
  "workflow": {
    "auto_plan": true,
    "create_subtasks": true
  }
}
```

**Priorität für Project Key:**
1. Explizit übergebener Parameter
2. `.claude-workflow.json` im Repo
3. `JIRA_PROJECT_KEY` aus `.env`

### Environment Variables (jira-mcp/.env)
```env
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@domain.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=PROJ
WORKER_POLL_INTERVAL=30
```

### Environment Variables (telegram-mcp/.env)
```env
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
JIRA_BASE_URL=https://your-domain.atlassian.net
```

### Prerequisites
1. **Jira Cloud Projekt** mit 9 Status-Spalten konfiguriert
2. **Jira API Token** von https://id.atlassian.com/manage-profile/security/api-tokens
3. **GitHub CLI (`gh`)** installiert und authentifiziert (`gh auth login`)
4. **Python 3.10+** mit pip

### Installation Paths
- Commands: `~/.claude/commands/workflow/`
- MCP Servers: `~/.claude/mcp-servers/`
- Settings: `~/.claude/settings.json`
- Database: `~/.claude/workflow-data/workflows.db` (legacy)

## Development Patterns

### Workflow Lifecycle (Jira-basiert)
1. `/workflow:start` erstellt Jira Issue mit Auto-Plan im Status PLANNED
2. User prüft Plan in Jira, fügt Kommentare hinzu
3. User verschiebt Issue nach PLANNED AND CONFIRMED
4. `/workflow:start-working` oder Worker verarbeitet automatisch
5. Bei REVIEW: GitHub Draft PR wird erstellt
6. Bei TESTING: Automatische Tests laufen
7. MANUAL TESTING: User testet manuell, verschiebt zu DOCUMENTATION
8. Bei DOCUMENTATION: Doku wird erstellt → DONE

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

## Language

The codebase and documentation are written in German. Workflow commands output German text.
