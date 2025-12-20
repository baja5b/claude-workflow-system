# Claude Workflow System - Windows Installation Script
# Run as Administrator for symlink creation

param(
    [switch]$Force,
    [string]$ClaudeDir = "$env:USERPROFILE\.claude"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Claude Workflow System Installer ===" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Target directories
$CommandsTarget = Join-Path $ClaudeDir "commands\workflow"
$McpServersTarget = Join-Path $ClaudeDir "mcp-servers"
$WorkflowDataDir = Join-Path $ClaudeDir "workflow-data"
$SettingsFile = Join-Path $ClaudeDir "settings.json"

# Source directories
$CommandsSource = Join-Path $ScriptDir "commands\workflow"
$McpServersSource = Join-Path $ScriptDir "mcp-servers"
$SchemaFile = Join-Path $ScriptDir "schemas\workflows.sql"

Write-Host "Source: $ScriptDir" -ForegroundColor Gray
Write-Host "Target: $ClaudeDir" -ForegroundColor Gray
Write-Host ""

# Check if running as Administrator (required for symlinks)
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "WARNING: Not running as Administrator. Will copy files instead of creating symlinks." -ForegroundColor Yellow
    Write-Host "For symlinks (recommended), run PowerShell as Administrator." -ForegroundColor Yellow
    Write-Host ""
}

# Create .claude directory if not exists
if (-not (Test-Path $ClaudeDir)) {
    Write-Host "Creating .claude directory..." -ForegroundColor Green
    New-Item -ItemType Directory -Path $ClaudeDir -Force | Out-Null
}

# Create commands directory
$CommandsParent = Split-Path $CommandsTarget -Parent
if (-not (Test-Path $CommandsParent)) {
    New-Item -ItemType Directory -Path $CommandsParent -Force | Out-Null
}

# Install commands
Write-Host "Installing workflow commands..." -ForegroundColor Green

if (Test-Path $CommandsTarget) {
    if ($Force) {
        Remove-Item $CommandsTarget -Recurse -Force
    } else {
        Write-Host "  Commands already exist. Use -Force to overwrite." -ForegroundColor Yellow
    }
}

if (-not (Test-Path $CommandsTarget)) {
    if ($isAdmin) {
        # Create symlink
        New-Item -ItemType SymbolicLink -Path $CommandsTarget -Target $CommandsSource | Out-Null
        Write-Host "  Created symlink: $CommandsTarget -> $CommandsSource" -ForegroundColor Gray
    } else {
        # Copy files
        Copy-Item -Path $CommandsSource -Destination $CommandsTarget -Recurse
        Write-Host "  Copied commands to: $CommandsTarget" -ForegroundColor Gray
    }
}

# Install MCP servers
Write-Host "Installing MCP servers..." -ForegroundColor Green

$mcpServers = @("docker-mcp", "scripts-mcp", "telegram-mcp", "workflow-mcp", "test-runner-mcp")
foreach ($server in $mcpServers) {
    $sourceDir = Join-Path $McpServersSource $server
    $targetDir = Join-Path $McpServersTarget $server

    if (-not (Test-Path $sourceDir)) {
        Write-Host "  Skipping $server (source not found)" -ForegroundColor Yellow
        continue
    }

    if (Test-Path $targetDir) {
        if ($Force) {
            Remove-Item $targetDir -Recurse -Force
        } else {
            Write-Host "  $server already exists. Use -Force to overwrite." -ForegroundColor Yellow
            continue
        }
    }

    if ($isAdmin) {
        New-Item -ItemType SymbolicLink -Path $targetDir -Target $sourceDir | Out-Null
        Write-Host "  Created symlink: $server" -ForegroundColor Gray
    } else {
        Copy-Item -Path $sourceDir -Destination $targetDir -Recurse
        Write-Host "  Copied: $server" -ForegroundColor Gray
    }
}

# Create workflow-data directory
Write-Host "Creating workflow data directory..." -ForegroundColor Green
if (-not (Test-Path $WorkflowDataDir)) {
    New-Item -ItemType Directory -Path $WorkflowDataDir -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $WorkflowDataDir "logs") -Force | Out-Null
}

# Initialize SQLite database
Write-Host "Initializing SQLite database..." -ForegroundColor Green
$DbFile = Join-Path $WorkflowDataDir "workflows.db"

if (-not (Test-Path $DbFile)) {
    if (Get-Command sqlite3 -ErrorAction SilentlyContinue) {
        sqlite3 $DbFile ".read `"$SchemaFile`""
        Write-Host "  Database initialized: $DbFile" -ForegroundColor Gray
    } else {
        Write-Host "  SQLite not found. Database will be created on first use." -ForegroundColor Yellow
        Write-Host "  Schema file: $SchemaFile" -ForegroundColor Gray
    }
} else {
    Write-Host "  Database already exists: $DbFile" -ForegroundColor Gray
}

# Update settings.json
Write-Host "Updating settings.json..." -ForegroundColor Green

$mcpConfig = @{
    mcpServers = @{
        docker = @{
            command = "python"
            args = @("$McpServersTarget\docker-mcp\server.py")
        }
        scripts = @{
            command = "python"
            args = @("$McpServersTarget\scripts-mcp\server.py")
        }
        telegram = @{
            command = "python"
            args = @("$McpServersTarget\telegram-mcp\server.py")
        }
        workflow = @{
            command = "python"
            args = @("$McpServersTarget\workflow-mcp\server.py")
        }
        "test-runner" = @{
            command = "python"
            args = @("$McpServersTarget\test-runner-mcp\server.py")
        }
    }
}

if (Test-Path $SettingsFile) {
    try {
        $existingSettings = Get-Content $SettingsFile -Raw | ConvertFrom-Json -AsHashtable

        if (-not $existingSettings.mcpServers) {
            $existingSettings.mcpServers = @{}
        }

        # Merge MCP servers (don't overwrite existing)
        foreach ($key in $mcpConfig.mcpServers.Keys) {
            if (-not $existingSettings.mcpServers.ContainsKey($key)) {
                $existingSettings.mcpServers[$key] = $mcpConfig.mcpServers[$key]
                Write-Host "  Added MCP server: $key" -ForegroundColor Gray
            } else {
                Write-Host "  MCP server already configured: $key" -ForegroundColor Gray
            }
        }

        $existingSettings | ConvertTo-Json -Depth 10 | Set-Content $SettingsFile
    } catch {
        Write-Host "  Warning: Could not parse existing settings.json" -ForegroundColor Yellow
    }
} else {
    $mcpConfig | ConvertTo-Json -Depth 10 | Set-Content $SettingsFile
    Write-Host "  Created new settings.json" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Installation Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Install Python dependencies:"
Write-Host "   pip install mcp python-telegram-bot paramiko" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Configure Telegram bot:"
Write-Host "   - Create bot via @BotFather"
Write-Host "   - Copy .env.example to .env in telegram-mcp/"
Write-Host "   - Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Test the installation:"
Write-Host "   - Open Claude Code in any project"
Write-Host "   - Run: /workflow-status" -ForegroundColor Gray
Write-Host ""

if (-not $isAdmin) {
    Write-Host "NOTE: Files were copied instead of symlinked." -ForegroundColor Yellow
    Write-Host "To use symlinks, run this script as Administrator." -ForegroundColor Yellow
}
