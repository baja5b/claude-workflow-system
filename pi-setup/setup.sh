#!/bin/bash
# Initial setup script for Raspberry Pi
# Run once after first deployment

set -e

INSTALL_DIR="/opt/workflow-system"
VENV_DIR="$INSTALL_DIR/venv"

echo "=== MusicTrackers Workflow System Setup ==="

# Create directory structure
sudo mkdir -p "$INSTALL_DIR"
sudo chown mcp:mcp "$INSTALL_DIR"

# Create Python virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate and install dependencies
source "$VENV_DIR/bin/activate"
pip install --upgrade pip

echo "Installing API dependencies..."
pip install -r "$INSTALL_DIR/api/requirements.txt"

echo "Installing Telegram bot dependencies..."
pip install -r "$INSTALL_DIR/telegram-bot/requirements.txt"

# Install systemd services
echo "Installing systemd services..."
sudo cp "$INSTALL_DIR/api/workflow-api.service" /etc/systemd/system/
sudo cp "$INSTALL_DIR/telegram-bot/telegram-bot.service" /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable workflow-api.service
sudo systemctl enable telegram-bot.service

# Start services
echo "Starting services..."
sudo systemctl start workflow-api.service
sudo systemctl start telegram-bot.service

# Wait and check status
sleep 3
echo ""
echo "=== Service Status ==="
systemctl is-active workflow-api.service || echo "workflow-api: not running"
systemctl is-active telegram-bot.service || echo "telegram-bot: not running"

echo ""
echo "=== API Health Check ==="
curl -s http://localhost:8100/health || echo "API not responding"

echo ""
echo "Setup complete!"
