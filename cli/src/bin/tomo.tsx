#!/usr/bin/env node
/**
 * Tomo CLI
 *
 * Admin management tool for the Tomo.
 * Uses React Ink for terminal UI rendering.
 *
 * Modes:
 * - Interactive (no args): Persistent TUI session
 * - One-shot (with args): Execute command and exit
 */

import { program } from 'commander';
import { render } from 'ink';
import React from 'react';

// Command components
import { CreateAdmin } from '../commands/admin/index.js';
import { ResetPassword } from '../commands/user/index.js';
import { ListLocked, Unlock } from '../commands/security/index.js';
import { Export, Import } from '../commands/backup/index.js';
import { List, Install, Status, Ping, Rotate } from '../commands/agent/index.js';
import { CheckUpdates } from '../commands/update/index.js';

// Interactive mode
import { App } from '../app/index.js';

/**
 * Check if we should run in interactive mode.
 * Interactive mode is used when no command is provided.
 */
function shouldRunInteractive(): boolean {
  const args = process.argv.slice(2);

  // No args = interactive mode
  if (args.length === 0) {
    return true;
  }

  // If only -m/--mcp-url is provided, still interactive
  if (args.length === 2 && (args[0] === '-m' || args[0] === '--mcp-url')) {
    return true;
  }

  return false;
}

/**
 * Get MCP URL from args if provided
 */
function getMcpUrlFromArgs(): string | undefined {
  const args = process.argv.slice(2);
  const mcpIndex = args.findIndex((a) => a === '-m' || a === '--mcp-url');

  if (mcpIndex !== -1 && args[mcpIndex + 1]) {
    return args[mcpIndex + 1];
  }

  return undefined;
}

// Check for interactive mode before setting up Commander
if (shouldRunInteractive()) {
  const mcpUrl = getMcpUrlFromArgs();
  render(<App mcpUrl={mcpUrl} />);
} else {
  // One-shot mode: use Commander for argument parsing

  program
    .name('tomo')
    .description('Tomo CLI - Admin management tool')
    .version('0.1.0');

  // ==========================================================================
  // Admin commands
  // ==========================================================================
  const admin = program.command('admin').description('Admin user management');

  admin
    .command('create')
    .description('Create a new admin user (initial setup or requires admin auth)')
    .option('-u, --username <username>', 'Admin username')
    .option('-p, --password <password>', 'Admin password')
    .option('-m, --mcp-url <url>', 'MCP server URL')
    .action((options) => {
      render(<CreateAdmin options={options} />);
    });

  // ==========================================================================
  // User commands
  // ==========================================================================
  const user = program.command('user').description('User management');

  user
    .command('reset-password')
    .description("Reset a user's password (requires admin auth)")
    .option('-u, --username <username>', 'Username')
    .option('-p, --password <password>', 'New password')
    .option('-m, --mcp-url <url>', 'MCP server URL')
    .action((options) => {
      render(<ResetPassword options={options} />);
    });

  // ==========================================================================
  // Security commands
  // ==========================================================================
  const security = program
    .command('security')
    .description('Security management');

  security
    .command('list-locked')
    .description('List all locked accounts (requires admin auth)')
    .option('--include-expired', 'Include expired locks')
    .option('--include-unlocked', 'Include manually unlocked accounts')
    .option('-m, --mcp-url <url>', 'MCP server URL')
    .action((options) => {
      render(<ListLocked options={options} />);
    });

  security
    .command('unlock')
    .description('Unlock a locked account (requires admin auth)')
    .option('-l, --lock-id <id>', 'Lock ID to unlock')
    .option('-a, --admin <username>', 'Admin username performing unlock')
    .option('-n, --notes <notes>', 'Optional notes about the unlock')
    .option('-m, --mcp-url <url>', 'MCP server URL')
    .action((options) => {
      render(<Unlock options={options} />);
    });

  // ==========================================================================
  // Backup commands
  // ==========================================================================
  const backup = program.command('backup').description('Backup and restore');

  backup
    .command('export')
    .description('Export encrypted backup (requires admin auth)')
    .option('-o, --output <path>', 'Output file path')
    .option('-p, --password <password>', 'Encryption password')
    .option('-m, --mcp-url <url>', 'MCP server URL')
    .action((options) => {
      render(<Export options={options} />);
    });

  backup
    .command('import')
    .description('Import backup from encrypted file (requires admin auth)')
    .option('-i, --input <path>', 'Input file path')
    .option('-p, --password <password>', 'Decryption password')
    .option('--overwrite', 'Overwrite existing data')
    .option('-m, --mcp-url <url>', 'MCP server URL')
    .action((options) => {
      render(<Import options={options} />);
    });

  // ==========================================================================
  // Agent commands
  // ==========================================================================
  const agent = program.command('agent').description('Agent management');

  agent
    .command('list')
    .description('List all agents (requires admin auth)')
    .option('-m, --mcp-url <url>', 'MCP server URL')
    .action((options) => {
      render(<List options={options} />);
    });

  agent
    .command('install <server-id>')
    .description('Install an agent on a server (requires admin auth)')
    .option('-m, --mcp-url <url>', 'MCP server URL')
    .action((serverId, options) => {
      render(<Install serverId={serverId} options={options} />);
    });

  agent
    .command('status <server-id>')
    .description('Get agent status for a server (requires admin auth)')
    .option('-m, --mcp-url <url>', 'MCP server URL')
    .action((serverId, options) => {
      render(<Status serverId={serverId} options={options} />);
    });

  agent
    .command('ping <server-id>')
    .description('Ping an agent to verify connectivity (requires admin auth)')
    .option('-t, --timeout <seconds>', 'Timeout in seconds', '5')
    .option('-m, --mcp-url <url>', 'MCP server URL')
    .action((serverId, options) => {
      render(<Ping serverId={serverId} options={options} />);
    });

  agent
    .command('rotate <server-id>')
    .description('Rotate agent authentication token (requires admin auth)')
    .option('-m, --mcp-url <url>', 'MCP server URL')
    .action((serverId, options) => {
      render(<Rotate serverId={serverId} options={options} />);
    });

  // ==========================================================================
  // Update command
  // ==========================================================================
  program
    .command('update')
    .description('Check for available updates (requires admin auth)')
    .option('-m, --mcp-url <url>', 'MCP server URL')
    .action((options) => {
      render(<CheckUpdates options={options} />);
    });

  // Parse and run
  program.parse();
}
