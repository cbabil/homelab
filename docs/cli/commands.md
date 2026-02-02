# Commands Reference

The CLI supports two modes: **Interactive mode** (persistent TUI) and **One-shot mode** (single command execution).

> **Note:** Most commands require admin authentication. You will be prompted for admin credentials when running commands.

## Global Options

| Option | Description |
|--------|-------------|
| `-V, --version` | Display version number |
| `-h, --help` | Display help information |
| `-m, --mcp-url <url>` | MCP server URL (default: `http://localhost:8000/mcp`) |

```bash
tomo --help
tomo --version
```

---

## Interactive Mode

Run `tomo` with no arguments (or only `-m`) to enter the persistent TUI:

```bash
# Default MCP URL
tomo

# Custom MCP URL
tomo -m http://192.168.1.100:8000/mcp
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Execute command |
| `Up/Down` | Navigate command history |
| `Ctrl+L` | Clear screen |
| `Ctrl+C` | Cancel current input |

### Slash Commands

These commands are available only in interactive mode:

| Command | Aliases | Description |
|---------|---------|-------------|
| `/help` | `/h`, `/?` | Show available commands |
| `/clear` | `/cls` | Clear output history |
| `/quit` | `/exit`, `/q` | Exit the CLI |
| `/status` | | Show connection status |
| `/servers` | | List all servers |
| `/agents` | | List all agents |
| `/login` | | Authenticate as admin |
| `/logout` | | Clear authentication |

### Regular Commands (Interactive Mode)

These commands work in both interactive and one-shot modes:

| Command | Description |
|---------|-------------|
| `agent list` | List all agents |
| `agent status <id>` | Get agent status |
| `agent ping <id>` | Ping an agent |
| `server list` | List all servers |
| `update` | Check for updates |

### Example Session

```
> /help
Available Commands:
  /help, /h, /?     - Show this help message
  /clear, /cls      - Clear output history
  /quit, /exit, /q  - Exit the CLI
  ...

> /servers
Found 2 server(s):
  [srv-1] Production Server (192.168.1.10) - online
  [srv-2] Dev Server (192.168.1.20) - offline

> agent list
Found 1 agent(s):
  [agent-1] Server: srv-1 - CONNECTED

> /quit
Goodbye!
```

---

## One-Shot Commands

Run `tomo <command>` to execute a single command and exit.

---

## `tomo admin`

Parent command for admin user management.

```bash
tomo admin --help
```

---

## `tomo admin create`

Create a new admin user account.

> **Authentication:** Requires admin authentication unless this is the initial system setup (no admin exists yet).

### Synopsis

```bash
tomo admin create [options]
```

### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `-u, --username <username>` | string | No* | (prompt) | Admin username |
| `-p, --password <password>` | string | No* | (prompt) | Admin password |
| `-m, --mcp-url <url>` | string | No | `http://localhost:8000/mcp` | MCP server URL |

*Required values are prompted interactively if not provided.

### Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| Username | Minimum 3 characters | "Username must be at least 3 characters" |
| Password | Minimum 8 characters | "Password must be at least 8 characters" |
| Confirm | Must match password | "Passwords do not match" |

### Examples

**Interactive mode (recommended):**

```bash
$ tomo admin create

╔═══════════════════════════════════════════════╗
║   Tomo - Admin CLI               ║
╚═══════════════════════════════════════════════╝

? Enter admin username: admin
? Enter admin password: ********
? Confirm password: ********
✔ Admin user created successfully
  Username: admin
```

**Non-interactive mode (for scripts):**

```bash
tomo admin create -u admin -p "MySecureP@ss123"
```

**With custom MCP server URL:**

```bash
tomo admin create -m http://192.168.1.100:8000/mcp -u admin -p "MySecureP@ss123"
```

**Partial options (prompts for missing):**

```bash
# Prompts only for password
tomo admin create -u admin
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (user exists, database not found, validation failed) |

### Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "User 'X' already exists" | Username taken | Choose different username |
| "Database not found" | DB not initialized | Run backend server first |
| "Username must be at least 3 characters" | Validation | Use longer username |
| "Password must be at least 8 characters" | Validation | Use longer password |
| "Passwords do not match" | Confirmation failed | Re-enter matching passwords |

---

## `tomo user`

Parent command for user management.

```bash
tomo user --help
```

---

## `tomo user reset-password`

Reset any user's password (admin or regular user).

> **Authentication:** Requires admin authentication.

### Synopsis

```bash
tomo user reset-password [options]
```

### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `-u, --username <username>` | string | No* | (prompt) | Username |
| `-p, --password <password>` | string | No* | (prompt) | New password |
| `-m, --mcp-url <url>` | string | No | `http://localhost:8000/mcp` | MCP server URL |

*Required values are prompted interactively if not provided.

### Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| Username | Must exist | "User 'X' not found" |
| Password | Minimum 8 characters | "Password must be at least 8 characters" |
| Confirm | Must match password | "Passwords do not match" |

### Examples

**Interactive mode (recommended):**

```bash
$ tomo user reset-password

╔═══════════════════════════════════════════════╗
║   Tomo - Admin CLI               ║
╚═══════════════════════════════════════════════╝

? Enter username: admin
? Enter new password: ********
? Confirm new password: ********
✔ Password reset successfully
  Username: admin
```

**Non-interactive mode (for scripts):**

```bash
tomo user reset-password -u admin -p "NewSecureP@ss456"
```

**With custom MCP server URL:**

```bash
tomo user reset-password -m http://192.168.1.100:8000/mcp -u john -p "NewSecureP@ss456"
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (user not found, validation failed) |

### Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "User 'X' not found" | Username doesn't exist | Check username spelling |
| "Database not found" | DB not initialized | Run backend server first |
| "Password must be at least 8 characters" | Validation | Use longer password |

---

## `tomo update`

Check for available updates from GitHub releases.

> **Authentication:** Requires admin authentication.

### Synopsis

```bash
tomo update [options]
```

### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `-m, --mcp-url <url>` | string | No | `http://localhost:8000/mcp` | MCP server URL |

### Examples

```bash
$ tomo update

╔═══════════════════════════════════════════════╗
║   Tomo - Admin CLI               ║
╚═══════════════════════════════════════════════╝

? Enter admin username: admin
? Enter admin password: ********

✔ Update check complete

Current versions:
  Backend:  1.0.0
  Frontend: 1.0.0
  API:      1.0.0

Latest version: 1.1.0

⚠ Update available!
  Release URL: https://github.com/tomo/tomo/releases/tag/v1.1.0
```

**When already up-to-date:**

```bash
$ tomo update

...

✔ You are running the latest version
```

**With custom MCP server URL:**

```bash
tomo update -m http://192.168.1.100:8000/mcp
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (displays version info and update status) |
| 1 | Error (authentication failed, network failure, MCP server unreachable) |

### Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Authentication failed" | Invalid admin credentials | Use correct admin username/password |
| "Failed to check for updates" | MCP server or GitHub API error | Check network connection and MCP server status |
| "MCP server unreachable" | Backend not running | Start the backend server first |

---

## `tomo agent`

Parent command for agent management.

```bash
tomo agent --help
```

---

## `tomo agent list`

List all registered agents.

> **Authentication:** Requires admin authentication.

### Synopsis

```bash
tomo agent list [options]
```

### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `-m, --mcp-url <url>` | string | No | `http://localhost:8000/mcp` | MCP server URL |

### Example

```bash
$ tomo agent list

╔═══════════════════════════════════════════════╗
║   Tomo - Admin CLI               ║
╚═══════════════════════════════════════════════╝

Found 2 agent(s):
────────────────────────────────────────────────
Agent ID: agent-abc123
  Server ID: srv-1
  Status: CONNECTED
  Version: 1.0.0
  Last Seen: 2024-01-15T10:30:00Z
────────────────────────────────────────────────
Agent ID: agent-def456
  Server ID: srv-2
  Status: DISCONNECTED
  Version: 1.0.0
  Last Seen: 2024-01-14T15:45:00Z
────────────────────────────────────────────────
```

---

## `tomo agent status <server-id>`

Get detailed status for an agent on a specific server.

> **Authentication:** Requires admin authentication.

### Synopsis

```bash
tomo agent status <server-id> [options]
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `server-id` | string | Yes | Server ID to check agent status |

### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `-m, --mcp-url <url>` | string | No | `http://localhost:8000/mcp` | MCP server URL |

### Example

```bash
$ tomo agent status srv-1

Agent Status for server srv-1:
  Status: CONNECTED
  Version: 1.0.0
  Last seen: 2024-01-15T10:30:00Z
```

---

## `tomo agent ping <server-id>`

Ping an agent to verify connectivity and measure latency.

> **Authentication:** Requires admin authentication.

### Synopsis

```bash
tomo agent ping <server-id> [options]
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `server-id` | string | Yes | Server ID to ping |

### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `-t, --timeout <seconds>` | number | No | `5` | Timeout in seconds |
| `-m, --mcp-url <url>` | string | No | `http://localhost:8000/mcp` | MCP server URL |

### Example

```bash
$ tomo agent ping srv-1

Pong! Agent on server srv-1 responded in 45ms
```

---

## `tomo agent install <server-id>`

Install an agent on a server.

> **Authentication:** Requires admin authentication.

### Synopsis

```bash
tomo agent install <server-id> [options]
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `server-id` | string | Yes | Server ID to install agent on |

### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `-m, --mcp-url <url>` | string | No | `http://localhost:8000/mcp` | MCP server URL |

---

## `tomo security`

Parent command for security management.

```bash
tomo security --help
```

---

## `tomo security list-locked`

List all locked user accounts.

> **Authentication:** Requires admin authentication.

### Synopsis

```bash
tomo security list-locked [options]
```

### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--include-expired` | boolean | No | `false` | Include expired locks |
| `--include-unlocked` | boolean | No | `false` | Include manually unlocked accounts |
| `-m, --mcp-url <url>` | string | No | `http://localhost:8000/mcp` | MCP server URL |

---

## `tomo security unlock`

Unlock a locked user account.

> **Authentication:** Requires admin authentication.

### Synopsis

```bash
tomo security unlock [options]
```

### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `-l, --lock-id <id>` | string | No* | (prompt) | Lock ID to unlock |
| `-a, --admin <username>` | string | No* | (prompt) | Admin username performing unlock |
| `-n, --notes <notes>` | string | No | | Optional notes about the unlock |
| `-m, --mcp-url <url>` | string | No | `http://localhost:8000/mcp` | MCP server URL |

---

## `tomo backup`

Parent command for backup and restore operations.

```bash
tomo backup --help
```

---

## `tomo backup export`

Export an encrypted backup of the system.

> **Authentication:** Requires admin authentication.

### Synopsis

```bash
tomo backup export [options]
```

### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `-o, --output <path>` | string | No* | (prompt) | Output file path |
| `-p, --password <password>` | string | No* | (prompt) | Encryption password |
| `-m, --mcp-url <url>` | string | No | `http://localhost:8000/mcp` | MCP server URL |

### Example

```bash
$ tomo backup export -o backup.enc

? Enter encryption password: ********
? Confirm password: ********
✔ Backup exported successfully to backup.enc
```

---

## `tomo backup import`

Import a backup from an encrypted file.

> **Authentication:** Requires admin authentication.

### Synopsis

```bash
tomo backup import [options]
```

### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `-i, --input <path>` | string | No* | (prompt) | Input file path |
| `-p, --password <password>` | string | No* | (prompt) | Decryption password |
| `--overwrite` | boolean | No | `false` | Overwrite existing data |
| `-m, --mcp-url <url>` | string | No | `http://localhost:8000/mcp` | MCP server URL |

### Example

```bash
$ tomo backup import -i backup.enc

? Enter decryption password: ********
✔ Backup imported successfully
```
