#!/usr/bin/env python3
"""
Telegram Bot für MusicTrackers Workflow-System

Dieser Bot läuft auf dem Raspberry Pi und:
1. Empfängt Befehle via Telegram
2. Speichert Tasks in der Workflow-API
3. Benachrichtigt dich über Workflow-Status

Befehle:
/start - Bot starten
/new <titel> - Neuen Workflow-Auftrag erstellen
/status - Alle aktiven Workflows anzeigen
/list - Offene Aufträge auflisten
/help - Hilfe anzeigen
"""

import os
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
except ImportError:
    print("ERROR: python-telegram-bot not installed. Run: pip install python-telegram-bot")
    exit(1)

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    exit(1)

from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Authorized chat ID
WORKFLOW_API_URL = os.getenv("WORKFLOW_API_URL", "http://localhost:8100")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store for pending tasks (created via Telegram, waiting for Claude Code)
pending_telegram_tasks = []


async def api_request(method: str, endpoint: str, data: dict = None) -> dict:
    """Make request to Workflow API."""
    url = f"{WORKFLOW_API_URL}{endpoint}"
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


def is_authorized(update: Update) -> bool:
    """Check if user is authorized."""
    if CHAT_ID:
        return str(update.effective_chat.id) == str(CHAT_ID)
    return True  # If no CHAT_ID configured, allow all


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if not is_authorized(update):
        await update.message.reply_text("⛔ Nicht autorisiert.")
        return

    welcome = """🎵 *MusicTrackers Workflow Bot*

Ich helfe dir, Entwicklungs-Aufträge zu erstellen und zu verfolgen.

*Befehle:*
/new `<titel>` - Neuen Auftrag erstellen
/status - Aktive Workflows anzeigen
/list - Alle offenen Aufträge
/pending - Unbearbeitete Telegram-Aufträge
/help - Diese Hilfe

*Beispiel:*
`/new Fix: Dashboard lädt nicht`

Der Auftrag wird gespeichert und wartet darauf, dass Claude Code ihn bearbeitet."""

    await update.message.reply_text(welcome, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    if not is_authorized(update):
        return

    help_text = """*Workflow-Bot Hilfe*

🆕 *Auftrag erstellen:*
`/new <titel>`
Erstellt einen neuen Workflow-Auftrag.

📋 *Status abfragen:*
`/status` - Zeigt aktive Workflows
`/list` - Alle Workflows auflisten
`/pending` - Telegram-Aufträge (noch nicht von Claude bearbeitet)

💡 *Tipps:*
- Aufträge werden automatisch an Claude Code gemeldet
- Du bekommst Benachrichtigungen bei wichtigen Statusänderungen
- Komplexe Aufträge sollten direkt in Claude Code gestartet werden"""

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def new_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /new command - create a new workflow task."""
    if not is_authorized(update):
        await update.message.reply_text("⛔ Nicht autorisiert.")
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Bitte gib einen Titel an.\n\nBeispiel: `/new Fix: Playlists laden nicht`",
            parse_mode="Markdown"
        )
        return

    title = " ".join(context.args)

    # Determine project from title (simple heuristics)
    project = "MusicTracker"  # Default
    if "workflow" in title.lower():
        project = "claude-workflow-system"

    # Create workflow via API
    result = await api_request("POST", "/workflows", {
        "project": project,
        "title": title,
        "requirements": json.dumps({
            "source": "telegram",
            "created_by": update.effective_user.username or "unknown",
            "created_at": datetime.now().isoformat(),
            "description": title
        })
    })

    if "error" in result:
        await update.message.reply_text(
            f"❌ Fehler beim Erstellen:\n`{result['error']}`",
            parse_mode="Markdown"
        )
        return

    workflow_id = result.get("workflow_id", "UNKNOWN")

    # Also store locally for pending list
    pending_telegram_tasks.append({
        "workflow_id": workflow_id,
        "title": title,
        "created_at": datetime.now().isoformat(),
        "status": "PENDING"
    })

    response = f"""✅ *Auftrag erstellt!*

*ID:* `{workflow_id}`
*Projekt:* {project}
*Titel:* {title}
*Status:* 📝 Waiting for Claude Code

Der Auftrag wartet darauf, dass du ihn in Claude Code mit `/workflow:status` abrufst und bearbeitest."""

    await update.message.reply_text(response, parse_mode="Markdown")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command - show active workflows."""
    if not is_authorized(update):
        return

    result = await api_request("GET", "/workflows/active")

    if "error" in result:
        await update.message.reply_text(f"❌ Fehler: {result['error']}")
        return

    if not result:
        await update.message.reply_text("📭 Keine aktiven Workflows.")
        return

    message = "*📊 Aktive Workflows:*\n\n"
    for wf in result[:10]:  # Limit to 10
        status_emoji = {
            "PLANNING": "📝",
            "CONFIRMED": "✅",
            "EXECUTING": "🔄",
            "TESTING": "🧪",
            "COMPLETED": "✅",
            "FAILED": "❌"
        }.get(wf.get("status", ""), "❓")

        message += f"{status_emoji} `{wf['workflow_id']}` - {wf.get('title', 'Untitled')}\n"
        message += f"   Status: {wf.get('status', 'Unknown')}\n\n"

    await update.message.reply_text(message, parse_mode="Markdown")


async def list_workflows(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /list command - list all recent workflows."""
    if not is_authorized(update):
        return

    result = await api_request("GET", "/workflows")

    if "error" in result:
        await update.message.reply_text(f"❌ Fehler: {result['error']}")
        return

    if not result:
        await update.message.reply_text("📭 Keine Workflows gefunden.")
        return

    message = "*📋 Alle Workflows:*\n\n"
    for wf in result[:15]:  # Limit to 15
        status_emoji = {
            "PLANNING": "📝",
            "CONFIRMED": "✅",
            "EXECUTING": "🔄",
            "TESTING": "🧪",
            "COMPLETED": "✅",
            "FAILED": "❌",
            "REJECTED": "🚫"
        }.get(wf.get("status", ""), "❓")

        message += f"{status_emoji} `{wf['workflow_id']}` {wf.get('title', 'Untitled')[:30]}\n"

    await update.message.reply_text(message, parse_mode="Markdown")


async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /pending command - show Telegram-created tasks."""
    if not is_authorized(update):
        return

    if not pending_telegram_tasks:
        await update.message.reply_text("📭 Keine wartenden Telegram-Aufträge.")
        return

    message = "*⏳ Wartende Telegram-Aufträge:*\n\n"
    for task in pending_telegram_tasks:
        message += f"• `{task['workflow_id']}` - {task['title']}\n"
        message += f"  Erstellt: {task['created_at'][:16]}\n\n"

    message += "_Diese Aufträge warten darauf, in Claude Code bearbeitet zu werden._"

    await update.message.reply_text(message, parse_mode="Markdown")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command - show workflow statistics."""
    if not is_authorized(update):
        return

    result = await api_request("GET", "/stats")

    if "error" in result:
        await update.message.reply_text(f"❌ Fehler: {result['error']}")
        return

    message = f"""*📈 Workflow-Statistiken*

📊 *Gesamt:* {result.get('total_workflows', 0)} Workflows
✅ *Abgeschlossen:* {result.get('completed', 0)}
🔄 *Aktiv:* {result.get('active', 0)}"""

    await update.message.reply_text(message, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle non-command messages."""
    if not is_authorized(update):
        return

    text = update.message.text

    # Interpret as new task if it looks like one
    if len(text) > 10 and any(word in text.lower() for word in ["fix", "add", "implement", "create", "update", "bug", "feature"]):
        await update.message.reply_text(
            f"💡 Soll ich das als neuen Auftrag erstellen?\n\nVerwende: `/new {text}`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🤖 Verwende /help um die verfügbaren Befehle zu sehen."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Exception while handling an update: {context.error}")
    if update and update.message:
        await update.message.reply_text("❌ Ein Fehler ist aufgetreten.")


def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        exit(1)

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("new", new_task))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("list", list_workflows))
    application.add_handler(CommandHandler("pending", pending))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Error handler
    application.add_error_handler(error_handler)

    # Start polling
    logger.info("Starting Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
