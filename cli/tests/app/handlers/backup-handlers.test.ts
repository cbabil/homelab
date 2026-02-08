/**
 * Tests for backup command handlers.
 */

import { describe, it, expect } from 'vitest';

import { handleBackupCommand } from '../../../src/app/handlers/backup-handlers.js';

describe('backup-handlers', () => {
  describe('export', () => {
    it('should return export signal with default path', async () => {
      const results = await handleBackupCommand('export', []);

      expect(results).toHaveLength(1);
      expect(results[0]!.type).toBe('system');
      expect(results[0]!.content).toBe('__BACKUP_EXPORT__./backup.enc');
    });

    it('should return export signal with custom path', async () => {
      const results = await handleBackupCommand('export', ['/tmp/my-backup.enc']);

      expect(results).toHaveLength(1);
      expect(results[0]!.content).toBe('__BACKUP_EXPORT__/tmp/my-backup.enc');
    });
  });

  describe('import', () => {
    it('should return import signal', async () => {
      const results = await handleBackupCommand('import', ['/tmp/backup.enc']);

      expect(results).toHaveLength(1);
      expect(results[0]!.type).toBe('system');
      expect(results[0]!.content).toBe('__BACKUP_IMPORT__/tmp/backup.enc');
    });

    it('should return overwrite import signal', async () => {
      const results = await handleBackupCommand('import', [
        '/tmp/backup.enc',
        '--overwrite',
      ]);

      expect(results).toHaveLength(1);
      expect(results[0]!.content).toBe(
        '__BACKUP_IMPORT_OVERWRITE__/tmp/backup.enc'
      );
    });

    it('should return error when path missing', async () => {
      const results = await handleBackupCommand('import', []);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Usage:');
    });
  });

  describe('path validation', () => {
    it('should reject paths with null bytes', async () => {
      const results = await handleBackupCommand('export', ['/tmp/bad\x00path']);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('invalid characters');
    });

    it('should accept absolute paths', async () => {
      const results = await handleBackupCommand('export', ['/tmp/backup.enc']);

      expect(results[0]!.content).toContain('__BACKUP_EXPORT__');
    });

    it('should accept relative paths', async () => {
      const results = await handleBackupCommand('export', ['./backup.enc']);

      expect(results[0]!.content).toContain('__BACKUP_EXPORT__');
    });
  });

  describe('unknown subcommand', () => {
    it('should return error for unknown subcommand', async () => {
      const results = await handleBackupCommand('unknown', []);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Unknown backup subcommand');
    });

    it('should return usage when no subcommand', async () => {
      const results = await handleBackupCommand('', []);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Usage:');
    });
  });
});
