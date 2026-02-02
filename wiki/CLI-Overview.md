# CLI Overview

The Tomo CLI provides command-line access to manage your Tomo installation.

---

## Installation

### DEB Package

The CLI is installed automatically with the DEB package:

```bash
tomo --help
```

### From Source

```bash
cd cli
bun install
bun run build
```

---

## Basic Usage

```bash
tomo <command> [subcommand] [options]
```

### Get Help

```bash
# General help
tomo --help

# Command help
tomo admin --help
tomo server --help
```

### Version

```bash
tomo --version
```

---

## Command Categories

| Category | Commands | Description |
|----------|----------|-------------|
| **Admin** | `admin create`, `admin reset-password` | Administrative tasks |
| **User** | `user list`, `user create` | User management |
| **Server** | `server list`, `server add` | Server management |
| **Agent** | `agent list`, `agent install` | Agent management |
| **App** | `app list`, `app deploy` | Application management |
| **Backup** | `backup export`, `backup import` | Backup operations |
| **Config** | `config show`, `config set` | Configuration |

---

## Quick Reference

### Admin Commands

```bash
tomo admin create              # Create admin account
tomo admin reset-password      # Reset admin password
```

### User Commands

```bash
tomo user list                 # List all users
tomo user create               # Create new user
tomo user delete --username X  # Delete user
tomo user unlock --username X  # Unlock locked user
```

### Server Commands

```bash
tomo server list               # List servers
tomo server add                # Add server
tomo server remove <id>        # Remove server
tomo server test <id>          # Test connection
```

### Agent Commands

```bash
tomo agent list                # List agents
tomo agent install <server>    # Install agent
tomo agent update <server>     # Update agent
tomo agent rotate-token <id>   # Rotate token
```

### Backup Commands

```bash
tomo backup export             # Create backup
tomo backup import <file>      # Restore backup
tomo backup list               # List backups
```

---

## Interactive Mode

Run CLI without arguments to enter interactive mode:

```bash
tomo
```

Features:
- Command history (up/down arrows)
- Tab completion
- Persistent session
- Rich output formatting

### Interactive Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/clear` | Clear screen |
| `/quit` | Exit |
| `/status` | Show connection status |

---

## Output Formats

### Default (Human-Readable)

```bash
tomo server list
```

Output:
```
ID    NAME              HOSTNAME       STATUS
1     Production        192.168.1.10   Online
2     Development       192.168.1.20   Offline
```

### JSON Output

```bash
tomo server list --json
```

Output:
```json
[
  {"id": 1, "name": "Production", "hostname": "192.168.1.10", "status": "online"},
  {"id": 2, "name": "Development", "hostname": "192.168.1.20", "status": "offline"}
]
```

### Quiet Mode

```bash
tomo server list --quiet
```

Output (IDs only):
```
1
2
```

---

## Global Options

| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help |
| `--version`, `-V` | Show version |
| `--json` | JSON output |
| `--quiet`, `-q` | Minimal output |
| `--verbose`, `-v` | Detailed output |
| `--config <file>` | Use config file |

---

## Configuration

### Config File

Default location: `~/.tomo/config.json`

```json
{
  "server": {
    "url": "http://localhost:8000"
  },
  "output": {
    "format": "table",
    "color": true
  }
}
```

### Environment Variables

```bash
TOMO_SERVER_URL=http://localhost:8000
TOMO_API_TOKEN=your-token
```

---

## Authentication

### Login

```bash
tomo login
```

Enter username and password when prompted.

### API Token

For scripts, use API token:

```bash
export TOMO_API_TOKEN=your-token
tomo server list
```

### Logout

```bash
tomo logout
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Authentication failed |
| 4 | Resource not found |
| 5 | Permission denied |

---

## Scripting Examples

### List Server IDs

```bash
tomo server list --quiet | while read id; do
  echo "Processing server $id"
  tomo server refresh "$id"
done
```

### Backup Script

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
tomo backup export --output "/backups/tomo-$DATE.backup"
```

### Health Check

```bash
if tomo server test "$SERVER_ID" --quiet; then
  echo "Server is online"
else
  echo "Server is offline"
  # Send alert
fi
```

---

## Detailed Command References

- [[CLI-Admin-Commands]] - Admin and user management
- [[CLI-Backup-Commands]] - Backup and restore
- [[CLI-Agent-Commands]] - Agent management

---

## Troubleshooting

### Command Not Found

```bash
# Check installation
which tomo

# If not found, add to PATH
export PATH=$PATH:/usr/local/bin
```

### Connection Failed

```bash
# Check server status
tomo status

# Verify server URL
tomo config show
```

### Authentication Error

```bash
# Re-login
tomo logout
tomo login
```

---

## Next Steps

- [[CLI-Admin-Commands]] - Admin commands
- [[CLI-Backup-Commands]] - Backup commands
- [[CLI-Agent-Commands]] - Agent commands
