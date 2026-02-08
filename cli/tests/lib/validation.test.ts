/**
 * Tests for validation module.
 */

import { describe, it, expect } from 'vitest';
import {
  validateUsername,
  validatePassword,
  validateMcpUrl,
  sanitizeForDisplay,
} from '../../src/lib/validation.js';

describe('validateUsername', () => {
  it('should accept valid username', () => {
    expect(validateUsername('admin')).toEqual({ valid: true });
  });

  it('should accept alphanumeric with hyphens and underscores', () => {
    expect(validateUsername('my-user_01')).toEqual({ valid: true });
  });

  it('should reject empty username', () => {
    const result = validateUsername('');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('required');
  });

  it('should reject short username', () => {
    const result = validateUsername('ab');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('3 characters');
  });

  it('should reject long username', () => {
    const result = validateUsername('a'.repeat(51));
    expect(result.valid).toBe(false);
    expect(result.error).toContain('50 characters');
  });

  it('should reject special characters', () => {
    const result = validateUsername('admin@home');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('letters, numbers');
  });

  it('should reject spaces', () => {
    const result = validateUsername('my user');
    expect(result.valid).toBe(false);
  });
});

describe('validatePassword', () => {
  it('should accept a strong password', () => {
    expect(validatePassword('MyP@ssw0rd123')).toEqual({ valid: true });
  });

  it('should reject empty password', () => {
    const result = validatePassword('');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('required');
  });

  it('should reject short password', () => {
    const result = validatePassword('Abc1!');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('12 characters');
  });

  it('should reject password without uppercase', () => {
    const result = validatePassword('mypassw0rd12!');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('uppercase');
  });

  it('should reject password without lowercase', () => {
    const result = validatePassword('MYPASSW0RD12!');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('lowercase');
  });

  it('should reject password without number', () => {
    const result = validatePassword('MyPassword!!xx');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('number');
  });

  it('should reject password without special character', () => {
    const result = validatePassword('MyPassword1234');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('special character');
  });

  it('should reject too long password', () => {
    const result = validatePassword('A'.repeat(100) + 'a1!' + 'x'.repeat(30));
    expect(result.valid).toBe(false);
    expect(result.error).toContain('128 characters');
  });
});

describe('validateMcpUrl', () => {
  it('should accept valid http URL', () => {
    expect(validateMcpUrl('http://localhost:8000/mcp')).toEqual({ valid: true });
  });

  it('should accept valid https URL', () => {
    expect(validateMcpUrl('https://api.example.com/mcp')).toEqual({ valid: true });
  });

  it('should reject non-http protocol', () => {
    const result = validateMcpUrl('ftp://example.com/mcp');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('http or https');
  });

  it('should reject invalid URL format', () => {
    const result = validateMcpUrl('not-a-url');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('Invalid URL');
  });

  it('should reject empty string', () => {
    const result = validateMcpUrl('');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('Invalid URL');
  });

  it('should reject javascript protocol', () => {
    const result = validateMcpUrl('javascript:alert(1)');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('http or https');
  });
});

describe('sanitizeForDisplay', () => {
  it('should return normal text unchanged', () => {
    expect(sanitizeForDisplay('hello world')).toBe('hello world');
  });

  it('should strip ANSI color codes', () => {
    expect(sanitizeForDisplay('\x1b[31mred text\x1b[0m')).toBe('red text');
  });

  it('should strip null bytes', () => {
    expect(sanitizeForDisplay('hello\x00world')).toBe('helloworld');
  });

  it('should strip control characters', () => {
    expect(sanitizeForDisplay('hello\x07\x08world')).toBe('helloworld');
  });

  it('should handle empty string', () => {
    expect(sanitizeForDisplay('')).toBe('');
  });

  it('should strip ANSI cursor movement sequences', () => {
    expect(sanitizeForDisplay('\x1b[2Ahello')).toBe('hello');
  });

  it('should strip OSC sequences', () => {
    expect(sanitizeForDisplay('\x1b]0;Window Title\x07hello')).toBe('hello');
  });

  it('should strip two-character escape sequences', () => {
    expect(sanitizeForDisplay('\x1b(Bhello\x1bMworld')).toBe('helloworld');
  });

  it('should strip OSC sequences terminated by ST', () => {
    expect(sanitizeForDisplay('\x1b]0;Window Title\x1b\\hello')).toBe('hello');
  });

  it('should strip nested/adjacent escape sequences', () => {
    expect(sanitizeForDisplay('\x1b[31m\x1b[1mbold red\x1b[0m')).toBe('bold red');
  });

  it('should strip charset designation at end of string', () => {
    expect(sanitizeForDisplay('hello\x1b(B')).toBe('hello');
  });

  it('should strip C1 control characters in 0x80-0x9F range', () => {
    expect(sanitizeForDisplay('hello\x8F\x90world')).toBe('helloworld');
  });
});
