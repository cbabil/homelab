# Tomo CLI

Command-line interface for managing Tomo users.

## Installation

### From Source

```bash
cd cli
npm install
npm run build
npm link
```

This makes the `tomo` command available globally.

### Unlink

```bash
npm unlink -g @tomo/cli
```

## Requirements

- Node.js 18+
- The backend database must be initialized (run the backend server first)

## Commands

### Admin Management

#### Create Admin User

```bash
tomo admin create
```

Creates a new admin user with interactive prompts for username, email, and password.

**Options:**
| Flag | Description |
|------|-------------|
| `-u, --username <username>` | Admin username |
| `-e, --email <email>` | Admin email |
| `-p, --password <password>` | Admin password |
| `-d, --data-dir <path>` | Custom data directory path |

**Examples:**

```bash
# Interactive mode
tomo admin create

# Non-interactive mode
tomo admin create -u admin -e admin@example.com -p securepassword123
```

### User Management

#### Reset User Password

```bash
tomo user reset-password
```

Resets any user's password (admin or regular user).

**Options:**
| Flag | Description |
|------|-------------|
| `-u, --username <username>` | Username |
| `-p, --password <password>` | New password |
| `-d, --data-dir <path>` | Custom data directory path |

**Examples:**

```bash
# Interactive mode
tomo user reset-password

# Non-interactive mode
tomo user reset-password -u admin -p newsecurepassword123
```

## Validation Rules

- **Username**: Minimum 3 characters
- **Email**: Valid email format
- **Password**: Minimum 8 characters

## Database Location

The CLI searches for the database in the following locations (in order):

1. Custom path (if provided via `--data-dir`)
2. `../backend/data/tomo.db` (relative to CLI)
3. `/var/lib/tomo/data/tomo.db`
4. `~/.tomo/data/tomo.db`

## Development

```bash
# Build
npm run build

# Run without global install
npm run dev -- admin create

# Clean build artifacts
npm run clean
```

## Project Structure

```
cli/
├── src/
│   ├── bin/
│   │   └── tomo.ts    # CLI entry point
│   └── lib/
│       ├── admin.ts      # Admin operations
│       └── db.ts         # Database connection
├── dist/                 # Compiled JavaScript
├── package.json
├── tsconfig.json
└── README.md
```
