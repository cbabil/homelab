#!/usr/bin/env node
/**
 * Tomo CLI
 *
 * Admin management tool for Tomo.
 * Uses React Ink for terminal UI rendering.
 *
 * All functionality is available via interactive slash commands.
 */

import { render } from 'ink';
import React from 'react';
import { fileURLToPath } from 'url';

import { App } from '../app/App.js';
import { validateMcpUrl } from '../lib/validation.js';
import { CLI_VERSION } from '../lib/constants.js';

/**
 * Get MCP URL from args if provided.
 * Validates the URL format and exits with error if invalid.
 */
function getMcpUrlFromArgs(): string | undefined {
  const args = process.argv.slice(2);
  const mcpIndex = args.findIndex((a) => a === '-m' || a === '--mcp-url');

  if (mcpIndex !== -1 && args[mcpIndex + 1]) {
    const url = args[mcpIndex + 1]!;
    const result = validateMcpUrl(url);
    if (!result.valid) {
      console.error(`Error: ${result.error}`);
      process.exit(1);
    }
    return url;
  }

  return undefined;
}

/**
 * Parse CLI args and launch the interactive TUI.
 * Exported for testing.
 */
export function run(): void {
  const args = process.argv.slice(2);

  if (args.includes('--version') || args.includes('-V')) {
    console.log(CLI_VERSION);
    process.exit(0);
  }

  if (args.includes('--help') || args.includes('-h')) {
    console.log(`Tomo CLI v${CLI_VERSION}`);
    console.log('');
    console.log('Usage: tomo [options]');
    console.log('');
    console.log('Options:');
    console.log('  -m, --mcp-url <url>  MCP server URL');
    console.log('  -V, --version        Show version');
    console.log('  -h, --help           Show help');
    process.exit(0);
  }

  const mcpUrl = getMcpUrlFromArgs();
  render(<App mcpUrl={mcpUrl} />);
}

// Only execute when run as the CLI entry point (not when imported by tests)
const currentFile = fileURLToPath(import.meta.url);
if (process.argv[1] === currentFile) {
  run();
}
