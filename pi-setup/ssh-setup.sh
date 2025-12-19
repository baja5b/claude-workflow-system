#!/bin/bash
# SSH Hardening Script for Raspberry Pi
# Run AFTER setting up SSH keys!

set -e

echo "=== SSH Hardening Script ==="
echo ""
echo "WARNING: This will disable password authentication!"
echo "Make sure you have SSH key access configured before running."
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Backup original config
echo "[1/3] Backing up SSH config..."
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak

# Configure SSH
echo "[2/3] Configuring SSH..."
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#*PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/^#*X11Forwarding.*/X11Forwarding no/' /etc/ssh/sshd_config

# Restart SSH
echo "[3/3] Restarting SSH service..."
sudo systemctl restart sshd

echo ""
echo "=== SSH Hardening Complete ==="
echo ""
echo "Settings applied:"
echo "- Password authentication: DISABLED"
echo "- Public key authentication: ENABLED"
echo "- Root login: DISABLED"
echo "- X11 forwarding: DISABLED"
echo ""
echo "Test your SSH connection in a new terminal before closing this one!"
