# Development

## Architecture

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Runtime | Node.js 18+ | JavaScript execution |
| Language | TypeScript | Type safety and maintainability |
| CLI Framework | Commander.js | Command parsing and help generation |
| Prompts | Inquirer.js | Interactive user input |
| Database | better-sqlite3 | Direct SQLite access |
| Password Hashing | bcrypt | Secure password storage |
| Styling | Chalk | Terminal colors and formatting |
| Spinners | Ora | Progress indicators |

### Project Structure

```
cli/
├── src/
│   ├── bin/
│   │   └── tomo.ts        # Entry point, command definitions
│   └── lib/
│       ├── admin.ts          # Admin CRUD operations
│       └── db.ts             # Database connection management
├── dist/                     # Compiled JavaScript (generated)
├── node_modules/             # Dependencies (generated)
├── package.json              # Package manifest
├── tsconfig.json             # TypeScript configuration
└── README.md                 # Quick reference
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Execution                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Input                                                     │
│      │                                                          │
│      ▼                                                          │
│  ┌──────────────┐                                               │
│  │  Commander   │  Parse command and options                    │
│  └──────────────┘                                               │
│      │                                                          │
│      ▼                                                          │
│  ┌──────────────┐                                               │
│  │  Inquirer    │  Prompt for missing values (interactive)      │
│  └──────────────┘                                               │
│      │                                                          │
│      ▼                                                          │
│  ┌──────────────┐                                               │
│  │  Validation  │  Username, email, password rules              │
│  └──────────────┘                                               │
│      │                                                          │
│      ▼                                                          │
│  ┌──────────────┐     ┌──────────────┐                          │
│  │    Admin     │────▶│    bcrypt    │  Hash password           │
│  │   Module     │     └──────────────┘                          │
│  └──────────────┘                                               │
│      │                                                          │
│      ▼                                                          │
│  ┌──────────────┐     ┌──────────────┐                          │
│  │     DB       │────▶│   SQLite     │  Execute query           │
│  │   Module     │     │   Database   │                          │
│  └──────────────┘     └──────────────┘                          │
│      │                                                          │
│      ▼                                                          │
│  ┌──────────────┐                                               │
│  │   Output     │  Success/error message with Chalk styling     │
│  └──────────────┘                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Setup

```bash
cd cli
npm install
```

## Scripts

| Script | Command | Description |
|--------|---------|-------------|
| `build` | `tsc` | Compile TypeScript to JavaScript |
| `start` | `node dist/bin/tomo.js` | Run compiled CLI |
| `dev` | `tsc && node dist/bin/tomo.js` | Build and run |
| `clean` | `rm -rf dist` | Remove build artifacts |
| `prepublishOnly` | `npm run build` | Build before publishing |

```bash
# Build
npm run build

# Run
npm run start -- --help

# Build and run
npm run dev -- admin create

# Clean
npm run clean
```

## Adding New Commands

### 1. Define Command

In `src/bin/tomo.ts`, add to the appropriate command group:

```typescript
admin
  .command('list')
  .description('List all admin users')
  .option('-d, --data-dir <path>', 'Data directory path')
  .action(async (options: ListOptions) => {
    console.log(banner);

    try {
      await initDatabase(options.dataDir);

      const spinner = ora('Fetching admin users...').start();
      const users = await listAdmins();
      spinner.succeed(chalk.green('Admin users:'));

      users.forEach(user => {
        console.log(chalk.gray(`  - ${user.username} (${user.email})`));
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      console.log(chalk.red('\n✗ Error:'), message);
      process.exit(1);
    } finally {
      closeDatabase();
    }
  });
```

### 2. Add Business Logic

In `src/lib/admin.ts`:

```typescript
export async function listAdmins(): Promise<User[]> {
  const db = getDatabase();
  const rows = db.prepare(
    'SELECT * FROM users WHERE role = ? ORDER BY username'
  ).all('admin') as User[];
  return rows;
}
```

### 3. Add Types

```typescript
interface ListOptions {
  dataDir?: string;
}
```

### 4. Build and Test

```bash
npm run build
node dist/bin/tomo.js admin list --help
node dist/bin/tomo.js admin list
```

## Type Definitions

### Core Interfaces

```typescript
// src/lib/admin.ts

interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  created_at: string;
  updated_at: string;
}

interface AdminResult {
  success: boolean;
  error?: string;
}
```

### Command Options

```typescript
// src/bin/tomo.ts

interface CreateOptions {
  username?: string;
  email?: string;
  password?: string;
  dataDir?: string;
}

interface ResetOptions {
  username?: string;
  password?: string;
  dataDir?: string;
}
```

## TypeScript Configuration

Key settings in `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "esModuleInterop": true,
    "outDir": "./dist",
    "rootDir": "./src"
  }
}
```

- **ES2022** - Modern JavaScript features
- **NodeNext** - ESM module support
- **strict** - Full type checking

## Code Style

### Conventions

- Use async/await for all async operations
- Handle errors with try/catch
- Use chalk for colored output
- Use ora for spinners
- Always close database connection in finally block

### Example Pattern

```typescript
.action(async (options: Options) => {
  console.log(banner);

  try {
    await initDatabase(options.dataDir);

    // Validation
    const existing = await getUser(username);
    if (!existing) {
      console.log(chalk.red('\n✗ Error:') + ' User not found');
      process.exit(1);
    }

    // Operation with spinner
    const spinner = ora('Processing...').start();
    const result = await doOperation();

    if (result.success) {
      spinner.succeed(chalk.green('Success'));
    } else {
      spinner.fail(chalk.red('Failed'));
      console.log(chalk.red(`  Error: ${result.error}`));
      process.exit(1);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.log(chalk.red('\n✗ Error:'), message);
    process.exit(1);
  } finally {
    closeDatabase();
  }
});
```

## Testing

### Manual Testing

```bash
# Create test database
mkdir -p test-data
sqlite3 test-data/tomo.db < ../backend/schema.sql

# Test commands
tomo admin create -d ./test-data -u testuser -e test@test.com -p testpass123
tomo user reset-password -d ./test-data -u testuser -p newpass123

# Clean up
rm -rf test-data
```

### Future: Automated Tests

Consider adding:

```bash
npm install --save-dev vitest @types/node
```

```typescript
// src/lib/admin.test.ts
import { describe, it, expect } from 'vitest';
import { createAdmin, getUser } from './admin';

describe('admin', () => {
  it('should create admin user', async () => {
    // Test implementation
  });
});
```

## Database Schema

The CLI interacts with the `users` table:

```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## Dependencies

### Production

| Package | Version | Purpose |
|---------|---------|---------|
| commander | ^12.0.0 | CLI framework |
| inquirer | ^9.2.0 | Interactive prompts |
| chalk | ^5.3.0 | Terminal styling |
| ora | ^8.0.0 | Spinners |
| better-sqlite3 | ^11.0.0 | SQLite driver |
| bcrypt | ^5.1.1 | Password hashing |
| uuid | ^9.0.0 | UUID generation |

### Development

| Package | Version | Purpose |
|---------|---------|---------|
| typescript | ^5.0.0 | TypeScript compiler |
| @types/node | ^20.0.0 | Node.js types |
| @types/bcrypt | ^5.0.2 | bcrypt types |
| @types/better-sqlite3 | ^7.6.0 | SQLite types |
| @types/inquirer | ^9.0.7 | Inquirer types |
| @types/uuid | ^9.0.0 | UUID types |

## Publishing

The CLI can be published to npm:

```bash
# Update version
npm version patch  # or minor, major

# Build
npm run build

# Publish
npm publish --access public
```

Users can then install globally:

```bash
npm install -g @tomo/cli
```
