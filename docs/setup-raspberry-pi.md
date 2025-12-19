# Raspberry Pi Docker Host Setup

Configure a dedicated Raspberry Pi as a Docker host for the Claude Workflow System.

## Hardware Requirements

- Raspberry Pi 4 (2GB+ RAM recommended)
- MicroSD Card (16GB minimum, 32GB recommended)
- Power Supply (Official 5V 3A)
- Ethernet cable or WiFi

## OS Installation

### 1. Flash Raspberry Pi OS Lite

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Select: **Raspberry Pi OS Lite (64-bit)**
3. Click gear icon for advanced options:
   - Set hostname: `docker-pi`
   - Enable SSH with password/key
   - Set username: `pi`
   - Configure WiFi (optional)
   - Set locale/timezone
4. Flash to SD card

### 2. First Boot

Insert SD card and power on. Wait 2-3 minutes.

Find IP address:
```bash
# From your Windows PC
ping docker-pi.local
# Or check your router's DHCP leases
```

## SSH Setup

### 1. Generate SSH Key (if not exists)

```powershell
# On Windows
ssh-keygen -t ed25519 -f ~/.ssh/docker-pi
```

### 2. Copy Key to Pi

```powershell
# Option 1: ssh-copy-id (Git Bash)
ssh-copy-id -i ~/.ssh/docker-pi.pub pi@docker-pi.local

# Option 2: Manual
cat ~/.ssh/docker-pi.pub | ssh pi@docker-pi.local "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### 3. Test Connection

```powershell
ssh -i ~/.ssh/docker-pi pi@docker-pi.local
```

## Docker Installation

SSH into the Pi and run:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose-plugin

# Reboot
sudo reboot
```

After reboot, verify:

```bash
docker --version
docker compose version
docker run hello-world
```

## Static IP (Recommended)

Edit DHCP config:

```bash
sudo nano /etc/dhcpcd.conf
```

Add at the end:

```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

Reboot:
```bash
sudo reboot
```

## Configure MCP Server

On your Windows PC, edit `mcp-servers/docker-mcp/.env`:

```env
DOCKER_HOST=192.168.1.100
DOCKER_SSH_PORT=22
DOCKER_SSH_USER=pi
DOCKER_SSH_KEY=~/.ssh/docker-pi
```

## Project Directory Structure

Create a directory for projects on the Pi:

```bash
sudo mkdir -p /opt/projects
sudo chown pi:pi /opt/projects
```

## Security Hardening

### 1. Disable Password Auth

```bash
sudo nano /etc/ssh/sshd_config
```

Set:
```
PasswordAuthentication no
PubkeyAuthentication yes
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

### 2. Setup Firewall

```bash
sudo apt install ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw enable
```

### 3. Automatic Updates

```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Monitoring

### Check Docker Status

```bash
docker ps
docker stats
```

### View System Resources

```bash
htop
df -h
```

### Docker Logs

```bash
docker logs <container_name>
```

## Troubleshooting

### Can't connect via SSH

1. Check Pi is powered and connected
2. Verify IP address: `ping docker-pi.local`
3. Check SSH key path in `.env`

### Docker permission denied

```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Out of disk space

```bash
# Clean Docker resources
docker system prune -a
docker volume prune
```

### Pi overheating

```bash
# Check temperature
vcgencmd measure_temp

# If >70°C, add cooling or reduce workload
```
