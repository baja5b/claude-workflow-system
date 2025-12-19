# Claude Workflow System

AI-gesteuertes Entwicklungs-Workflow-System für Claude Code mit:
- Requirements Planning mit AI-Brainstorming
- Confirmation Gate vor Implementierung
- Task Queue mit sequentieller Verarbeitung
- 4-Augen-Prinzip (unabhängige Test-Instanz)
- Auto-Dokumentation und Cleanup
- Mobile Notifications via Telegram

## Quick Start

### Windows Installation

```powershell
git clone https://github.com/yourusername/claude-workflow-system
cd claude-workflow-system
.\install.ps1
```

### Manuelle Installation

1. Kopiere `commands/workflow/` nach `C:\Users\<user>\.claude\commands\`
2. Kopiere `mcp-servers/` nach `C:\Users\<user>\.claude\mcp-servers\`
3. Merge `mcp-servers/settings.example.json` in deine `settings.json`
4. Installiere Python Dependencies: `pip install -r mcp-servers/*/requirements.txt`

## Verfügbare Commands

| Command | Beschreibung |
|---------|--------------|
| `/workflow-start <title>` | Neuen Workflow starten |
| `/workflow-status` | Status des aktuellen Workflows |
| `/workflow-plan` | AI Brainstorming für Requirements |
| `/workflow-confirm` | Plan bestätigen und Ausführung starten |
| `/workflow-execute` | Tasks manuell fortsetzen |
| `/workflow-test` | 4-Augen Test triggern |
| `/workflow-document` | Dokumentation generieren |
| `/workflow-cleanup` | Deprecated Code entfernen |

## Architektur

```
┌─────────────────┐         ┌─────────────────────┐
│  Windows PC     │   SSH   │  Raspberry Pi       │
│  (Claude Code)  │ ──────▶ │  (Docker Host)      │
│                 │         │                     │
│  MCP Server     │         │  - Docker Engine    │
│  docker-mcp     │         │  - 24/7 Betrieb     │
│                 │         │  - Alle Projekte    │
└─────────────────┘         └─────────────────────┘
```

### MCP Server

| Server | Funktion |
|--------|----------|
| `github` | Issues, PRs, Commits automatisieren |
| `docker` | Container auf Raspberry Pi steuern |
| `scripts` | Lokale Automatisierungen ausführen |
| `telegram` | Handy-Benachrichtigungen |

## Workflow-Status

```
PLANNING → CONFIRMED → EXECUTING → TESTING → DOCUMENTING → COMPLETED
    ↓         ↓           ↓          ↓           ↓
 REJECTED   FAILED      FAILED     FAILED      FAILED
```

## Beispiel-Workflow

```
User: /workflow-start "Dark Mode Toggle für MusicTracker"

Claude: === REQUIREMENTS PLANNING ===
Fragen zur Klärung:
1. Soll Dark Mode in localStorage persistieren?
2. System-Preference als Default?

User: Ja, Ja

Claude: === PROPOSED PLAN ===
Tasks:
1. ThemeContext erstellen
2. ThemeToggle Komponente
3. Unit Tests

[Telegram: "Neuer Workflow gestartet: Dark Mode Toggle"]

User: /workflow-confirm

Claude: Starte Execution...
[1/3] ThemeContext... COMPLETED
[2/3] ThemeToggle... COMPLETED
[3/3] Tests... COMPLETED

=== 4-AUGEN TEST ===
- [PASS] Dark Mode Toggle existiert
- [PASS] Tests bestanden

[Telegram: "Workflow erfolgreich!"]
```

## Setup

### Telegram Bot

1. @BotFather in Telegram öffnen
2. `/newbot` - Bot erstellen
3. Token kopieren
4. Nachricht an Bot senden
5. Chat ID holen: `https://api.telegram.org/bot<TOKEN>/getUpdates`
6. In `mcp-servers/telegram-mcp/.env` eintragen

### Raspberry Pi (Docker Host)

Siehe [docs/setup-raspberry-pi.md](docs/setup-raspberry-pi.md)

## Entwicklung

```bash
# MCP Server testen
cd mcp-servers/telegram-mcp
pip install -r requirements.txt
python server.py

# Tests ausführen
pytest mcp-servers/*/tests/
```

## Lizenz

MIT License
