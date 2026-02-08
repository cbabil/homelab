/**
 * Tests for user command handlers.
 */

import { describe, it, expect } from 'vitest';

import { handleUserCommand } from '../../../src/app/handlers/user-handlers.js';

describe('user-handlers', () => {
  describe('reset-password', () => {
    it('should return reset password signal', async () => {
      const results = await handleUserCommand('reset-password', ['john']);

      expect(results).toHaveLength(1);
      expect(results[0]!.type).toBe('system');
      expect(results[0]!.content).toBe('__RESET_PASSWORD__john');
    });

    it('should return error when username missing', async () => {
      const results = await handleUserCommand('reset-password', []);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Usage:');
    });
  });

  describe('unknown subcommand', () => {
    it('should return error for unknown subcommand', async () => {
      const results = await handleUserCommand('unknown', []);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Unknown user subcommand');
    });

    it('should return usage when no subcommand', async () => {
      const results = await handleUserCommand('', []);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Usage:');
    });
  });
});
