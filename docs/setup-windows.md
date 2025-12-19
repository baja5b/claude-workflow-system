# Windows Setup Guide

## Prerequisites

- Windows 10/11
- Python 3.10+
- Git
- Claude Code (VS Code Extension)

## Installation

### 1. Clone Repository

```powershell
cd E:\Users\<username>\Repository
git clone https://github.com/yourusername/claude-workflow-system
cd claude-workflow-system
```

### 2. Run Installation Script

**As Administrator (recommended for symlinks):**

```powershell
# Right-click PowerShell -> Run as Administrator
.\install.ps1
```

**As normal user (copies files):**

```powershell
.\install.ps1
```

### 3. Install Python Dependencies

```powershell
pip install mcp httpx python-dotenv paramiko
```

### 4. Configure Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow instructions
3. Copy the bot token
4. Send a message to your new bot
5. Get your chat ID:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
6. Create `.env` file:
   ```powershell
   cp mcp-servers/telegram-mcp/.env.example mcp-servers/telegram-mcp/.env
   ```
7. Edit `.env` with your token and chat ID

### 5. Configure Docker Host (Optional)

If using a Raspberry Pi as Docker host:

```powershell
cp mcp-servers/docker-mcp/.env.example mcp-servers/docker-mcp/.env
# Edit with your Pi's IP and SSH settings
```

## Verify Installation

### Check Commands

Open Claude Code in any project and type:

```
/workflow-status
```

Should show "No active workflow" message.

### Check MCP Servers

In Claude Code settings, verify `mcpServers` are configured:

```json
{
  "mcpServers": {
    "telegram": {...},
    "docker": {...},
    "scripts": {...}
  }
}
```

### Test Telegram

```powershell
cd mcp-servers/telegram-mcp
python -c "
from server import send_telegram_message
import asyncio
asyncio.run(send_telegram_message('Test from Claude Workflow System'))
"
```

## Troubleshooting

### "mcp module not found"

```powershell
pip install mcp
```

### "Permission denied" for symlinks

Run PowerShell as Administrator, or use `.\install.ps1 -Force` to copy instead.

### Telegram not working

1. Check bot token is correct
2. Verify chat ID (must be numeric)
3. Make sure you've sent at least one message to the bot first

### SSH to Raspberry Pi fails

1. Check IP address is correct
2. Verify SSH key is set up: `ssh -i ~/.ssh/id_rsa pi@<ip>`
3. Check firewall allows port 22

## Updating

```powershell
cd E:\Users\<username>\Repository\claude-workflow-system
git pull
.\install.ps1 -Force
```
