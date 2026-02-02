# CLI Architecture

## Overview

The Tomo CLI uses [Ink](https://github.com/vadimdemedes/ink) - a React-based terminal UI framework - to provide an interactive command-line experience. This is the same approach used by Claude Code and other modern CLI tools.

## Technology Stack

| Package | Purpose |
|---------|---------|
| `ink` | React for CLI - TUI rendering framework |
| `react` | Component model and state management |
| `commander` | CLI argument parsing and command routing |
| `zod` | Schema validation for inputs |
| `chalk` | Terminal colors (bundled with ink) |

## Directory Structure

```
cli/
├── src/
│   ├── bin/
│   │   └── tomo.tsx          # Entry point - routes interactive/one-shot
│   ├── app/                      # Interactive mode components
│   │   ├── App.tsx              # Main persistent TUI application
│   │   ├── OutputHistory.tsx    # Scrollable output area
│   │   ├── InputArea.tsx        # Command input with history
│   │   ├── StatusBar.tsx        # Connection and auth status
│   │   ├── CommandRouter.ts     # Command parsing and routing
│   │   ├── types.ts             # Shared types for interactive mode
│   │   └── index.ts             # Barrel export
│   ├── components/
│   │   ├── ui/                   # Reusable UI components
│   │   │   ├── Banner.tsx
│   │   │   ├── Spinner.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── TextInput.tsx
│   │   │   ├── PasswordInput.tsx
│   │   │   ├── Confirm.tsx
│   │   │   └── index.ts
│   │   └── common/               # Shared command components
│   │       ├── ErrorDisplay.tsx
│   │       ├── SuccessDisplay.tsx
│   │       └── index.ts
│   ├── commands/                 # One-shot command implementations
│   │   ├── admin/
│   │   │   ├── CreateAdmin.tsx
│   │   │   └── index.ts
│   │   ├── user/
│   │   │   ├── ResetPassword.tsx
│   │   │   └── index.ts
│   │   ├── security/
│   │   │   ├── ListLocked.tsx
│   │   │   ├── Unlock.tsx
│   │   │   └── index.ts
│   │   ├── backup/
│   │   │   ├── Export.tsx
│   │   │   ├── Import.tsx
│   │   │   └── index.ts
│   │   ├── agent/
│   │   │   ├── List.tsx
│   │   │   ├── Install.tsx
│   │   │   ├── Status.tsx
│   │   │   ├── Ping.tsx
│   │   │   └── index.ts
│   │   └── update/
│   │       └── CheckUpdates.tsx
│   ├── hooks/                    # Custom React hooks
│   │   ├── useMCP.ts             # MCP client connection
│   │   ├── useAuth.ts            # Authentication state
│   │   └── index.ts
│   ├── lib/                      # Business logic
│   │   ├── admin.ts
│   │   ├── agent.ts
│   │   ├── auth.ts
│   │   ├── backup.ts
│   │   ├── mcp-client.ts
│   │   ├── patch.ts
│   │   └── security.ts
│   └── types/
│       └── index.ts              # Shared TypeScript types
├── tests/
│   ├── bin/
│   ├── lib/
│   └── components/               # Component tests
└── package.json
```

## Component Architecture

### Entry Point (`tomo.tsx`)

The entry point detects whether to run in interactive or one-shot mode:

```tsx
#!/usr/bin/env node
import { program } from 'commander';
import { render } from 'ink';
import React from 'react';
import { App } from '../app/index.js';
import { CreateAdmin } from './commands/admin/CreateAdmin.js';

// Interactive mode when no args (or only -m)
if (shouldRunInteractive()) {
  render(<App mcpUrl={getMcpUrlFromArgs()} />);
} else {
  // One-shot mode: use Commander
  program
    .command('admin create')
    .description('Create a new admin user')
    .option('-u, --username <username>')
    .option('-p, --password <password>')
    .action((options) => {
      render(<CreateAdmin options={options} />);
    });

  program.parse();
}
```

### Interactive Mode Architecture

The interactive mode consists of a persistent TUI with three regions:

```
╔═══════════════════════════════════════════════╗
║        Tomo - Admin CLI          ║  <- Header
╠═══════════════════════════════════════════════╣
│                                               │
│  Output/History Area (scrollable)             │  <- OutputHistory
│  - Command results                            │
│  - Server responses                           │
│                                               │
├───────────────────────────────────────────────┤
│ MCP: Connected | User: admin                  │  <- StatusBar
├───────────────────────────────────────────────┤
│ > _                                           │  <- InputArea
╚═══════════════════════════════════════════════╝
```

#### App.tsx - Main Application

Manages global state and renders the layout:

```tsx
interface AppState {
  mcpConnected: boolean;
  mcpUrl: string;
  authenticated: boolean;
  username: string | null;
  history: OutputMessage[];
  inputValue: string;
  commandHistory: string[];
  historyIndex: number;
  isRunningCommand: boolean;
}
```

#### OutputHistory.tsx - Scrollable Output

- Stores array of output messages with timestamps
- Supports keyboard scrolling (up/down, Page Up/Down)
- Auto-scrolls to bottom on new messages
- Color-coded by message type (info, success, error, command)

#### InputArea.tsx - Command Input

- Single-line text input with prompt
- Command history navigation (up/down arrows)
- Disabled state during command execution

#### StatusBar.tsx - Status Display

- MCP connection status (connected/connecting/error)
- Authentication status and username
- Keyboard shortcuts hint

#### CommandRouter.ts - Command Dispatcher

Parses input and routes to appropriate handlers:

- Slash commands: `/help`, `/quit`, `/servers`, `/agents`, etc.
- Regular commands: `agent list`, `update`, etc.
- Returns results as `CommandResult[]` for display

### UI Components

#### Spinner

```tsx
import { Box, Text } from 'ink';
import Spinner from 'ink-spinner';

export function LoadingSpinner({ text }: { text: string }) {
  return (
    <Box>
      <Text color="cyan">
        <Spinner type="dots" />
      </Text>
      <Text> {text}</Text>
    </Box>
  );
}
```

#### TextInput

```tsx
import { Box, Text } from 'ink';
import TextInput from 'ink-text-input';
import { useState } from 'react';

interface Props {
  label: string;
  onSubmit: (value: string) => void;
  mask?: boolean;
}

export function Input({ label, onSubmit, mask }: Props) {
  const [value, setValue] = useState('');

  return (
    <Box>
      <Text color="cyan">? </Text>
      <Text>{label}: </Text>
      <TextInput
        value={value}
        onChange={setValue}
        onSubmit={onSubmit}
        mask={mask ? '*' : undefined}
      />
    </Box>
  );
}
```

#### Select Menu

```tsx
import { Box, Text, useInput } from 'ink';
import { useState } from 'react';

interface Option {
  label: string;
  value: string;
}

interface Props {
  options: Option[];
  onSelect: (value: string) => void;
}

export function Select({ options, onSelect }: Props) {
  const [selectedIndex, setSelectedIndex] = useState(0);

  useInput((input, key) => {
    if (key.upArrow) {
      setSelectedIndex((i) => Math.max(0, i - 1));
    }
    if (key.downArrow) {
      setSelectedIndex((i) => Math.min(options.length - 1, i + 1));
    }
    if (key.return) {
      onSelect(options[selectedIndex].value);
    }
  });

  return (
    <Box flexDirection="column">
      {options.map((option, index) => (
        <Box key={option.value}>
          <Text color={index === selectedIndex ? 'cyan' : 'white'}>
            {index === selectedIndex ? '❯ ' : '  '}
            {option.label}
          </Text>
        </Box>
      ))}
    </Box>
  );
}
```

### Command Components

Each command is a self-contained React component that manages its own state:

```tsx
import { Box, Text, useApp } from 'ink';
import { useState, useEffect } from 'react';
import { LoadingSpinner } from '../components/ui/Spinner.js';
import { Banner } from '../components/ui/Banner.js';
import { Input } from '../components/ui/Input.js';
import { createAdmin } from '../lib/admin.js';

interface Props {
  options: {
    username?: string;
    password?: string;
    mcpUrl?: string;
  };
}

type Step = 'username' | 'password' | 'confirm' | 'creating' | 'done' | 'error';

export function CreateAdmin({ options }: Props) {
  const { exit } = useApp();
  const [step, setStep] = useState<Step>('username');
  const [username, setUsername] = useState(options.username || '');
  const [password, setPassword] = useState(options.password || '');
  const [error, setError] = useState<string | null>(null);

  // Skip input steps if values provided via CLI
  useEffect(() => {
    if (options.username && options.password) {
      setStep('creating');
    } else if (options.username) {
      setStep('password');
    }
  }, []);

  // Handle create admin
  useEffect(() => {
    if (step === 'creating') {
      createAdmin(username, password)
        .then((result) => {
          if (result.success) {
            setStep('done');
          } else {
            setError(result.error || 'Unknown error');
            setStep('error');
          }
        })
        .catch((err) => {
          setError(err.message);
          setStep('error');
        });
    }
  }, [step]);

  // Exit after done/error
  useEffect(() => {
    if (step === 'done' || step === 'error') {
      setTimeout(() => exit(), 100);
    }
  }, [step]);

  return (
    <Box flexDirection="column">
      <Banner />

      {step === 'username' && (
        <Input
          label="Enter admin username"
          onSubmit={(value) => {
            setUsername(value);
            setStep('password');
          }}
        />
      )}

      {step === 'password' && (
        <Input
          label="Enter admin password"
          mask
          onSubmit={(value) => {
            setPassword(value);
            setStep('confirm');
          }}
        />
      )}

      {step === 'confirm' && (
        <Input
          label="Confirm password"
          mask
          onSubmit={(value) => {
            if (value === password) {
              setStep('creating');
            } else {
              setError('Passwords do not match');
              setStep('password');
            }
          }}
        />
      )}

      {step === 'creating' && (
        <LoadingSpinner text="Creating admin user..." />
      )}

      {step === 'done' && (
        <Box>
          <Text color="green">✔ </Text>
          <Text>Admin user created successfully</Text>
        </Box>
      )}

      {step === 'error' && (
        <Box>
          <Text color="red">✗ Error: </Text>
          <Text>{error}</Text>
        </Box>
      )}
    </Box>
  );
}
```

## Hooks

### useMCP Hook

Manages MCP client connection lifecycle:

```tsx
import { useState, useEffect, useCallback } from 'react';
import { initMCPClient, closeMCPClient, getMCPClient } from '../lib/mcp-client.js';

export function useMCP(mcpUrl?: string) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const url = mcpUrl || process.env.MCP_SERVER_URL || 'http://localhost:8000/mcp';
    initMCPClient(url)
      .then(() => setConnected(true))
      .catch((err) => setError(err.message));

    return () => {
      closeMCPClient();
    };
  }, [mcpUrl]);

  const callTool = useCallback(async (tool: string, args?: Record<string, unknown>) => {
    const client = getMCPClient();
    return client.callTool(tool, args);
  }, []);

  return { connected, error, callTool };
}
```

### useAuth Hook

Manages authentication state:

```tsx
import { useState, useCallback } from 'react';
import { checkSystemSetup, authenticateAdmin } from '../lib/auth.js';

export function useAuth() {
  const [authenticated, setAuthenticated] = useState(false);
  const [needsSetup, setNeedsSetup] = useState<boolean | null>(null);

  const checkSetup = useCallback(async () => {
    const result = await checkSystemSetup();
    setNeedsSetup(result);
    return result;
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const result = await authenticateAdmin();
    setAuthenticated(result);
    return result;
  }, []);

  return { authenticated, needsSetup, checkSetup, login };
}
```

## Testing

Tests use `ink-testing-library` for component testing:

```tsx
import { render } from 'ink-testing-library';
import { CreateAdmin } from '../commands/admin/CreateAdmin.js';

describe('CreateAdmin', () => {
  it('should prompt for username when not provided', () => {
    const { lastFrame } = render(<CreateAdmin options={{}} />);
    expect(lastFrame()).toContain('Enter admin username');
  });

  it('should skip to password when username provided', () => {
    const { lastFrame } = render(
      <CreateAdmin options={{ username: 'admin' }} />
    );
    expect(lastFrame()).toContain('Enter admin password');
  });
});
```

## Migration Strategy

1. **Phase 1: Setup**
   - Install Ink dependencies
   - Configure TypeScript for JSX
   - Create base UI components

2. **Phase 2: Component Migration**
   - Convert each command one at a time
   - Keep lib/ files unchanged (business logic)
   - Test each command after conversion

3. **Phase 3: Testing**
   - Add ink-testing-library
   - Update existing tests
   - Add component tests

4. **Phase 4: Cleanup**
   - Remove inquirer, ora dependencies
   - Update documentation
   - Final testing

## Benefits

- **React Mental Model**: Familiar component-based architecture
- **Declarative UI**: State-driven rendering
- **Testable**: Components can be unit tested
- **Composable**: Reusable UI components
- **Modern**: Same approach as Claude Code
