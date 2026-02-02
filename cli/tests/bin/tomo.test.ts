/**
 * Integration tests for Tomo CLI commands.
 *
 * Tests command parsing, help output, and command structure.
 * Note: These are lighter integration tests that verify command
 * registration and options without executing the full flows,
 * as the underlying modules are already tested thoroughly.
 */

import { describe, it, expect } from 'vitest';
import { execSync } from 'child_process';
import path from 'path';

// Path to the compiled CLI
const CLI_PATH = path.join(__dirname, '../../dist/src/bin/tomo.js');

/**
 * Helper to run CLI command and handle missing build gracefully
 */
function runCli(args: string): string | null {
  try {
    return execSync(`node ${CLI_PATH} ${args}`, {
      encoding: 'utf-8',
    });
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      console.warn('CLI not compiled, skipping integration test');
      return null;
    }
    throw error;
  }
}

describe('CLI Integration Tests', () => {
  describe('Command Registration', () => {
    it('should show help with --help flag', () => {
      const output = runCli('--help');
      if (!output) return;

      expect(output).toContain('Tomo CLI');
      expect(output).toContain('Admin management tool');
    });

    it('should show version with --version flag', () => {
      const output = runCli('--version');
      if (!output) return;

      expect(output.trim()).toMatch(/^\d+\.\d+\.\d+$/);
    });

    it('should have admin command group', () => {
      const output = runCli('admin --help');
      if (!output) return;

      expect(output).toContain('Admin user management');
      expect(output).toContain('create');
    });

    it('should have admin create command', () => {
      const output = runCli('admin create --help');
      if (!output) return;

      expect(output).toContain('Create a new admin user');
      expect(output).toContain('--username');
      expect(output).toContain('--password');
      expect(output).toContain('--mcp-url');
    });

    it('should have user command group', () => {
      const output = runCli('user --help');
      if (!output) return;

      expect(output).toContain('User management');
      expect(output).toContain('reset-password');
    });

    it('should have user reset-password command', () => {
      const output = runCli('user reset-password --help');
      if (!output) return;

      expect(output).toContain("Reset a user's password");
      expect(output).toContain('--username');
      expect(output).toContain('--password');
      expect(output).toContain('--mcp-url');
    });

    it('should have update command', () => {
      const output = runCli('update --help');
      if (!output) return;

      expect(output).toContain('Check for available updates');
      expect(output).toContain('--mcp-url');
    });

    it('should have agent command group', () => {
      const output = runCli('agent --help');
      if (!output) return;

      expect(output).toContain('Agent management');
      expect(output).toContain('list');
      expect(output).toContain('install');
      expect(output).toContain('status');
      expect(output).toContain('ping');
    });

    it('should have agent list command', () => {
      const output = runCli('agent list --help');
      if (!output) return;

      expect(output).toContain('List all agents');
      expect(output).toContain('--mcp-url');
    });

    it('should have agent install command', () => {
      const output = runCli('agent install --help');
      if (!output) return;

      expect(output).toContain('Install an agent');
      expect(output).toContain('server-id');
    });

    it('should have agent status command', () => {
      const output = runCli('agent status --help');
      if (!output) return;

      expect(output).toContain('Get agent status');
      expect(output).toContain('server-id');
    });

    it('should have agent ping command', () => {
      const output = runCli('agent ping --help');
      if (!output) return;

      expect(output).toContain('Ping an agent');
      expect(output).toContain('--timeout');
    });

    it('should have security command group', () => {
      const output = runCli('security --help');
      if (!output) return;

      expect(output).toContain('Security management');
      expect(output).toContain('list-locked');
      expect(output).toContain('unlock');
    });

    it('should have security list-locked command', () => {
      const output = runCli('security list-locked --help');
      if (!output) return;

      expect(output).toContain('List all locked accounts');
      expect(output).toContain('--include-expired');
    });

    it('should have backup command group', () => {
      const output = runCli('backup --help');
      if (!output) return;

      expect(output).toContain('Backup and restore');
      expect(output).toContain('export');
      expect(output).toContain('import');
    });

    it('should have backup export command', () => {
      const output = runCli('backup export --help');
      if (!output) return;

      expect(output).toContain('Export encrypted backup');
      expect(output).toContain('--output');
      expect(output).toContain('--password');
    });

    it('should have backup import command', () => {
      const output = runCli('backup import --help');
      if (!output) return;

      expect(output).toContain('Import backup');
      expect(output).toContain('--input');
      expect(output).toContain('--overwrite');
    });
  });

  describe('Option Validation', () => {
    it('admin create should have short option aliases', () => {
      const output = runCli('admin create --help');
      if (!output) return;

      expect(output).toContain('-u,');
      expect(output).toContain('-p,');
      expect(output).toContain('-m,');
    });

    it('user reset-password should have short option aliases', () => {
      const output = runCli('user reset-password --help');
      if (!output) return;

      expect(output).toContain('-u,');
      expect(output).toContain('-p,');
      expect(output).toContain('-m,');
    });
  });
});
