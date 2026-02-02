# Tomo CLI Reference

The Tomo CLI provides administrative tools for managing servers, agents, users, and system updates.

## Installation

The CLI is included with the Tomo installation. It requires Node.js 18+ and connects to the MCP backend server.

```bash
cd cli
npm install
npm run build
npm link  # Optional: makes 'tomo' available globally
```

## Usage

The CLI supports two modes:

### Interactive Mode (Default)

Run without arguments to enter the persistent TUI:

```bash
tomo
```

This opens an interactive session where you can run multiple commands without re-authenticating.

### One-Shot Mode

Run with a command to execute and exit:

```bash
tomo <command> [options]
```

## Global Options

| Option | Description |
|--------|-------------|
| `-V, --version` | Display version number |
| `-h, --help` | Display help for command |
| `-m, --mcp-url <url>` | MCP server URL (default: `http://localhost:8000/mcp`) |

---

## Interactive Mode

When running `tomo` without arguments, you enter a persistent TUI session:

```
╔═══════════════════════════════════════════════╗
║        Tomo - Admin CLI          ║
╠═══════════════════════════════════════════════╣
│  Welcome to Tomo CLI             │
│  Type /help for available commands            │
├───────────────────────────────────────────────┤
│ MCP: Connected | User: admin                  │
├───────────────────────────────────────────────┤
│ > _                                           │
╚═══════════════════════════════════════════════╝
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Execute command |
| `Up/Down` | Navigate command history |
| `Ctrl+L` | Clear screen |
| `Ctrl+C` | Cancel current input |

### Slash Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear output history |
| `/quit` | Exit the CLI |
| `/status` | Show connection status |
| `/servers` | List all servers |
| `/agents` | List all agents |
| `/logout` | Clear authentication |

### Regular Commands (in Interactive Mode)

| Command | Description |
|---------|-------------|
| `agent list` | List all agents |
| `agent status <id>` | Get agent status |
| `agent ping <id>` | Ping an agent |
| `server list` | List all servers |
| `update` | Check for updates |

---

## One-Shot Commands

## Commands

### `tomo admin create`

Create a new admin user.

**Usage:**
```bash
tomo admin create [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-u, --username <username>` | Admin username (min 3 characters) |
| `-p, --password <password>` | Admin password (min 8 characters) |
| `-m, --mcp-url <url>` | MCP server URL |

**Authentication:**
- **Initial setup**: No authentication required (creates first admin)
- **After setup**: Requires admin authentication

**Examples:**

Interactive mode:
```bash
tomo admin create
```

Non-interactive mode:
```bash
tomo admin create -u admin -p MySecurePassword123
```

With custom MCP URL:
```bash
tomo admin create -m http://192.168.1.100:8000/mcp
```

---

### `tomo user reset-password`

Reset a user's password.

**Usage:**
```bash
tomo user reset-password [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-u, --username <username>` | Username of account to reset |
| `-p, --password <password>` | New password (min 8 characters) |
| `-m, --mcp-url <url>` | MCP server URL |

**Authentication:**
- Requires admin authentication

**Examples:**

Interactive mode:
```bash
tomo user reset-password
```

Non-interactive mode:
```bash
tomo user reset-password -u john -p NewSecurePassword456
```

---

### `tomo update`

Check for available system updates.

**Usage:**
```bash
tomo update [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-m, --mcp-url <url>` | MCP server URL |

**Authentication:**
- Requires admin authentication

**Output:**
- Current versions (Backend, Frontend, API)
- Latest available version
- Update status and release URL (if update available)

**Example:**
```bash
tomo update
```

Sample output:
```
╔═══════════════════════════════════════════════╗
║   Tomo - Admin CLI               ║
╚═══════════════════════════════════════════════╝

✔ Update check complete

Current versions:
  Backend:  0.1.0
  Frontend: 0.1.0
  API:      v1

Latest version: 0.1.0

✔ You are running the latest version
```

---

### `tomo agent list`

List all registered agents.

**Usage:**
```bash
tomo agent list [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-m, --mcp-url <url>` | MCP server URL |

**Authentication:** Requires admin authentication.

---

### `tomo agent status <server-id>`

Get agent status for a specific server.

**Usage:**
```bash
tomo agent status <server-id> [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-m, --mcp-url <url>` | MCP server URL |

---

### `tomo agent ping <server-id>`

Ping an agent to verify connectivity.

**Usage:**
```bash
tomo agent ping <server-id> [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-t, --timeout <seconds>` | Timeout in seconds (default: 5) |
| `-m, --mcp-url <url>` | MCP server URL |

---

### `tomo agent install <server-id>`

Install an agent on a server.

**Usage:**
```bash
tomo agent install <server-id> [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-m, --mcp-url <url>` | MCP server URL |

---

### `tomo security list-locked`

List all locked user accounts.

**Usage:**
```bash
tomo security list-locked [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--include-expired` | Include expired locks |
| `--include-unlocked` | Include manually unlocked accounts |
| `-m, --mcp-url <url>` | MCP server URL |

---

### `tomo security unlock`

Unlock a locked user account.

**Usage:**
```bash
tomo security unlock [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-l, --lock-id <id>` | Lock ID to unlock |
| `-a, --admin <username>` | Admin username performing unlock |
| `-n, --notes <notes>` | Optional notes about the unlock |
| `-m, --mcp-url <url>` | MCP server URL |

---

### `tomo backup export`

Export an encrypted backup.

**Usage:**
```bash
tomo backup export [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-o, --output <path>` | Output file path |
| `-p, --password <password>` | Encryption password |
| `-m, --mcp-url <url>` | MCP server URL |

---

### `tomo backup import`

Import a backup from an encrypted file.

**Usage:**
```bash
tomo backup import [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-i, --input <path>` | Input file path |
| `-p, --password <password>` | Decryption password |
| `--overwrite` | Overwrite existing data |
| `-m, --mcp-url <url>` | MCP server URL |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_SERVER_URL` | MCP backend server URL | `http://localhost:8000/mcp` |

## Exit Codes

| Code | Description |
|------|-------------|
| `0` | Success |
| `1` | Error (authentication failed, user exists, etc.) |

## Authentication Flow

1. CLI prompts for admin credentials
2. Credentials are verified against the MCP server
3. If valid, the requested operation proceeds
4. Invalid credentials result in exit code 1

## Troubleshooting

### Connection refused

Ensure the MCP backend is running:
```bash
cd backend
python src/main.py
```

### Authentication failed

- Verify username and password are correct
- Ensure the user has admin role
- Check that the MCP server URL is correct

### Command not found

Build the CLI first:
```bash
cd cli
yarn build
```

Or run directly with:
```bash
yarn tomo <command>
```

## Security Notes

1. **Password handling**: Passwords are never logged or displayed
2. **Initial setup**: The first admin can be created without authentication
3. **Subsequent admins**: Require existing admin authentication
4. **Network**: Use HTTPS in production environments
