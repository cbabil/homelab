# Tomo CLI

Interactive terminal UI for managing Tomo infrastructure.

## Installation

### From Source

```bash
cd cli
bun install
bun run build
bun link
```

This makes the `tomo` command available globally.

### Unlink

```bash
bun unlink @tomo/cli
```

## Requirements

- [Bun](https://bun.sh) (latest)
- A running Tomo backend (MCP server)

## Usage

```bash
# Launch interactive TUI
tomo

# Launch with custom MCP server URL
tomo -m http://custom-host:8000/mcp

# Show version
tomo --version
```

All commands are entered as slash commands inside the interactive TUI:

### Available Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/status` | Show connection status |
| `/servers` | List all servers |
| `/agents` | List all agents |
| `/login` | Authenticate as admin |
| `/logout` | Clear authentication |
| `/view <tab>` | Switch view (dashboard, agents, logs, settings) |
| `/refresh` | Force data refresh |
| `/clear` | Clear output history |
| `/quit` | Exit the CLI |

### Management Commands

| Command | Description |
|---------|-------------|
| `/agent list` | List all agents |
| `/agent install <server>` | Install agent on a server |
| `/agent status <server>` | Get agent status |
| `/agent ping <server>` | Ping agent connectivity |
| `/agent rotate <server>` | Rotate agent auth token |
| `/server list` | List all servers |
| `/update` | Check for updates |
| `/security list-locked` | List locked accounts |
| `/security unlock <id>` | Unlock a locked account |
| `/backup export [path]` | Export encrypted backup |
| `/backup import <path>` | Import backup from file |
| `/user reset-password <user>` | Reset a user's password |
| `/admin create` | Initial admin setup |

## Development

```bash
# Build
bun run build

# Run in dev mode
bun run dev

# Run tests
bun run test

# Watch tests
bun run test:watch

# Clean build artifacts
bun run clean
```

## Project Structure

```
cli/
├── src/
│   ├── app/              # Interactive TUI (React Ink)
│   │   ├── handlers/     # Command handler functions
│   │   ├── views/        # Dashboard views
│   │   ├── App.tsx        # Main app component
│   │   ├── CommandRouter.ts # Slash command routing
│   │   └── signals.ts     # Signal constants
│   ├── bin/
│   │   └── tomo.tsx       # CLI entry point
│   ├── components/        # Shared UI components
│   │   ├── dashboard/     # Dashboard panels
│   │   ├── common/        # Reusable components
│   │   └── ui/            # Base UI elements
│   ├── hooks/             # React hooks
│   └── lib/               # MCP client, auth, utilities
├── tests/                 # Test files (mirrors src/)
├── dist/                  # Compiled JavaScript
├── package.json
├── tsconfig.json
└── README.md
```
