# Telegram Bot Setup

Step-by-step guide to create and configure a Telegram bot for workflow notifications.

## Create Bot

### 1. Open BotFather

1. Open Telegram
2. Search for `@BotFather`
3. Start a chat

### 2. Create New Bot

Send to BotFather:
```
/newbot
```

Follow the prompts:
- **Name**: `Claude Workflow Bot` (display name)
- **Username**: `your_claude_workflow_bot` (must end in `bot`)

### 3. Save Token

BotFather will respond with:
```
Done! Congratulations on your new bot. You will find it at t.me/your_claude_workflow_bot.
Use this token to access the HTTP API:
123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

**Copy and save this token!**

## Get Chat ID

### 1. Start Chat with Bot

1. Click the bot link or search for your bot
2. Click **Start** or send any message

### 2. Get Updates

Open in browser:
```
https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```

Replace `<YOUR_TOKEN>` with your actual token.

### 3. Find Chat ID

Look for:
```json
{
  "result": [{
    "message": {
      "chat": {
        "id": 987654321,  // <-- This is your chat ID
        "first_name": "Your Name",
        "type": "private"
      }
    }
  }]
}
```

## Configure MCP Server

### 1. Create .env File

```bash
cd mcp-servers/telegram-mcp
cp .env.example .env
```

### 2. Edit .env

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
```

## Test Bot

### Quick Test (Python)

```python
import httpx
import asyncio

TOKEN = "your_token"
CHAT_ID = "your_chat_id"

async def test():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": "Hello from Claude Workflow System!",
        "parse_mode": "Markdown"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        print(response.json())

asyncio.run(test())
```

### Test via MCP Server

```bash
cd mcp-servers/telegram-mcp
pip install -r requirements.txt
python server.py
```

Then use tool call:
```json
{
  "name": "telegram_send",
  "arguments": {
    "message": "Test notification"
  }
}
```

## Notification Types

The bot supports these notification types:

### Workflow Start
```
🚀 Workflow gestartet
Projekt: MusicTracker
Task: Dark Mode Toggle
Status: Planning
```

### Workflow Complete
```
✅ Workflow abgeschlossen
Projekt: MusicTracker
Task: Dark Mode Toggle
Dauer: 12 min
Tests: 24/24 passed
```

### Workflow Error
```
❌ Fehler aufgetreten
Projekt: MusicTracker
Task: Dark Mode Toggle
Phase: Testing
Error: npm test failed
```

### Decision Required
```
❓ Entscheidung erforderlich
Workflow: Dark Mode Toggle
Frage: System-Preference als Default?
→ Öffne Claude Code zum Antworten
```

## Customize Bot

### Set Bot Description

Send to @BotFather:
```
/setdescription
```
Select your bot and enter:
```
Sends workflow notifications from Claude Code
```

### Set Bot Avatar

Send to @BotFather:
```
/setuserpic
```
Upload an image.

### Set Bot Commands

Send to @BotFather:
```
/setcommands
```
Enter:
```
status - Get current workflow status
help - Show help message
```

## Group Chat (Optional)

To use in a group:

1. Add bot to group
2. Get group chat ID (will be negative number like `-123456789`)
3. Update `.env` with group chat ID

**Note**: Bot must be admin in groups with "Privacy mode" enabled.

## Troubleshooting

### "Chat not found"

- Make sure you've sent at least one message to the bot
- Verify chat ID is correct (numeric, no quotes)

### "Unauthorized"

- Check bot token is correct
- Token should include the `:` separator

### Messages not received

1. Check Python environment has correct packages
2. Verify `.env` file is in correct location
3. Test API directly in browser first

### Rate limits

Telegram limits:
- 30 messages/second to same chat
- 20 messages/minute to same group

For workflows, this is rarely an issue.
