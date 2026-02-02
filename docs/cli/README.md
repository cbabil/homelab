# Tomo CLI Documentation

Command-line interface for managing Tomo.

## Overview

The Tomo CLI is a Node.js-based terminal user interface (TUI) for managing your tomo. It supports two modes:

- **Interactive mode**: A persistent TUI session with command history, scrollable output, and real-time status
- **One-shot mode**: Execute single commands for scripting and automation

### Features

- Persistent interactive TUI with scrollable output
- Command history navigation (up/down arrows)
- Real-time MCP connection and auth status display
- Slash commands for quick actions (`/help`, `/servers`, `/agents`)
- One-shot mode for scripting and automation
- Interactive prompts with password masking
- Input validation with helpful error messages

### Why a Separate CLI?

The CLI operates independently from the web interface, allowing administrators to:

1. **Recover access** - Reset admin passwords when locked out of the web interface
2. **Initial setup** - Create the first admin user before the web UI is accessible
3. **Automation** - Script user management in CI/CD or provisioning workflows
4. **Security** - Perform admin operations without exposing endpoints over the network
5. **Quick management** - List servers, agents, and check status without opening a browser

## Documentation

| Document | Description |
|----------|-------------|
| [Installation](./installation.md) | Prerequisites, install, update, and uninstall |
| [Commands](./commands.md) | Full command reference with examples |
| [Configuration](./configuration.md) | Database paths and options |
| [Security](./security.md) | Password handling and best practices |
| [Troubleshooting](./troubleshooting.md) | Common issues and solutions |
| [Development](./development.md) | Architecture, contributing, adding commands |

## Quick Start

```bash
# Install
cd cli
npm install && npm run build && npm link

# Start interactive mode
tomo

# Or run one-shot commands
tomo admin create
tomo agent list
tomo --help
```

## Modes

### Interactive Mode (default)

Run `tomo` with no arguments to enter the persistent TUI:

```
╔═══════════════════════════════════════════════╗
║        Tomo - Admin CLI          ║
╠═══════════════════════════════════════════════╣
│  Welcome to Tomo CLI             │
│  Type /help for available commands            │
├───────────────────────────────────────────────┤
│ MCP: Connected | User: Not authenticated      │
├───────────────────────────────────────────────┤
│ > _                                           │
╚═══════════════════════════════════════════════╝
```

### One-Shot Mode

Run `tomo <command>` to execute a single command and exit:

```bash
tomo admin create -u admin -p MyPassword123
tomo agent list
tomo update
```

## Commands Summary

| Command | Description |
|---------|-------------|
| `tomo` | Start interactive mode |
| `tomo admin create` | Create a new admin user |
| `tomo user reset-password` | Reset any user's password |
| `tomo agent list` | List all agents |
| `tomo agent status <id>` | Get agent status |
| `tomo agent ping <id>` | Ping an agent |
| `tomo security list-locked` | List locked accounts |
| `tomo security unlock` | Unlock an account |
| `tomo backup export` | Export encrypted backup |
| `tomo backup import` | Import backup |
| `tomo update` | Check for updates |

See [Commands Reference](./commands.md) for full details.
