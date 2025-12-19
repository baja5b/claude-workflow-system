#!/bin/bash
# Raspberry Pi Docker Installation Script
# Run as: ./install-docker.sh

set -e

echo "=== Raspberry Pi Docker Setup ==="
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "[1/5] Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install Docker
echo "[2/5] Installing Docker..."
if command -v docker &> /dev/null; then
    echo "Docker already installed: $(docker --version)"
else
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
fi

# Add user to docker group
echo "[3/5] Configuring user permissions..."
sudo usermod -aG docker $USER

# Install Docker Compose
echo "[4/5] Installing Docker Compose..."
sudo apt install -y docker-compose-plugin

# Create project directory
echo "[5/5] Creating project directory..."
sudo mkdir -p /opt/projects
sudo chown $USER:$USER /opt/projects

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Docker version: $(docker --version)"
echo "Docker Compose version: $(docker compose version)"
echo ""
echo "IMPORTANT: Log out and back in (or reboot) to apply group changes."
echo ""
echo "After reboot, test with: docker run hello-world"
