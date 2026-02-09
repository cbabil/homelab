/**
 * Tests for help command handler.
 */

import { describe, it, expect } from 'vitest';
import { getHelpText } from '../../../src/app/handlers/help-handler.js';

describe('getHelpText', () => {
  it('should return a non-empty array of CommandResult', () => {
    const results = getHelpText();
    expect(results.length).toBeGreaterThan(0);
  });

  it('should contain info and system type entries', () => {
    const results = getHelpText();
    const types = new Set(results.map((r) => r.type));
    expect(types.has('info')).toBe(true);
    expect(types.has('system')).toBe(true);
  });

  it('should contain expected navigation commands', () => {
    const results = getHelpText();
    const content = results.map((r) => r.content).join('\n');
    expect(content).toContain('/help');
    expect(content).toContain('/clear');
    expect(content).toContain('/quit');
    expect(content).toContain('/status');
    expect(content).toContain('/login');
    expect(content).toContain('/logout');
    expect(content).toContain('/view');
    expect(content).toContain('/refresh');
  });

  it('should contain expected management commands', () => {
    const results = getHelpText();
    const content = results.map((r) => r.content).join('\n');
    expect(content).toContain('/agent');
    expect(content).toContain('/server');
    expect(content).toContain('/update');
    expect(content).toContain('/security');
    expect(content).toContain('/backup');
    expect(content).toContain('/user');
    expect(content).toContain('/admin');
  });

  it('should include command aliases', () => {
    const results = getHelpText();
    const content = results.map((r) => r.content).join('\n');
    expect(content).toContain('/h');
    expect(content).toContain('/?');
    expect(content).toContain('/cls');
    expect(content).toContain('/exit');
    expect(content).toContain('/q');
  });

  it('should have section headers', () => {
    const results = getHelpText();
    const content = results.map((r) => r.content).join('\n');
    expect(content).toContain('Available Commands:');
    expect(content).toContain('Management Commands:');
  });

  it('should only use valid MessageType values', () => {
    const results = getHelpText();
    const validTypes = ['info', 'success', 'error', 'system'];
    for (const result of results) {
      expect(validTypes).toContain(result.type);
    }
  });
});
