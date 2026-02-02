# Installation

## Prerequisites

- **Node.js 18+** - Required runtime
- **npm** - Package manager (included with Node.js)
- **Initialized database** - Run the backend server at least once

## Install from Source

```bash
# Navigate to CLI directory
cd cli

# Install dependencies
npm install

# Build TypeScript
npm run build

# Link globally
npm link
```

## Verify Installation

```bash
tomo --version
# Output: 0.1.0

tomo --help
```

## Uninstall

```bash
# Remove global link
npm unlink -g @tomo/cli

# Or from the cli directory
cd cli
npm unlink
```

## Update

```bash
cd cli
git pull
npm install
npm run build
```

## Run Without Installing Globally

If you prefer not to install globally:

```bash
# Build first
cd cli
npm run build

# Run directly
node dist/bin/tomo.js --help

# Or use npm script
npm run start -- --help
npm run dev -- admin create
```

## Troubleshooting Installation

### "command not found: tomo"

The CLI is not linked globally. Run:

```bash
cd cli
npm link
```

Or add the CLI's bin directory to your PATH.

### "npm link" permission errors

On some systems, you may need sudo:

```bash
sudo npm link
```

Or configure npm to use a different directory:

```bash
npm config set prefix ~/.npm-global
export PATH=~/.npm-global/bin:$PATH
npm link
```

### Build errors

Ensure you have the correct Node.js version:

```bash
node --version  # Should be 18+
```

Clean and rebuild:

```bash
npm run clean
npm install
npm run build
```
