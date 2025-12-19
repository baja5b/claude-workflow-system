# Raspberry Pi Setup Scripts

Scripts to quickly set up a Raspberry Pi as a Docker host.

## Quick Start

```bash
# SSH into Pi
ssh pi@docker-pi.local

# Download and run setup
curl -fsSL https://raw.githubusercontent.com/yourusername/claude-workflow-system/main/pi-setup/install-docker.sh | bash
```

## Scripts

### install-docker.sh

Installs Docker and Docker Compose on a fresh Raspberry Pi OS.

```bash
./install-docker.sh
```

**What it does:**
- Updates system packages
- Installs Docker from official script
- Adds user to docker group
- Installs Docker Compose plugin
- Creates project directory at `/opt/projects`

### ssh-setup.sh

Hardens SSH configuration.

```bash
./ssh-setup.sh
```

**What it does:**
- Disables password authentication
- Enables only key-based auth
- Sets secure SSH options
- Restarts SSH service

**Note**: Run this AFTER setting up SSH keys!

## Manual Steps

After running scripts:

1. **Reboot**: `sudo reboot`
2. **Set static IP** (see docs/setup-raspberry-pi.md)
3. **Configure firewall** (recommended)
4. **Test Docker**: `docker run hello-world`
