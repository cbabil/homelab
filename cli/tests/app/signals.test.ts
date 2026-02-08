/**
 * Tests for signal constants and helpers.
 */

import { describe, it, expect } from 'vitest';
import { SIGNALS, parseSignal } from '../../src/app/signals.js';

describe('SIGNALS', () => {
  it('should define all expected signal constants', () => {
    expect(SIGNALS.CLEAR).toBe('__CLEAR__');
    expect(SIGNALS.LOGOUT).toBe('__LOGOUT__');
    expect(SIGNALS.LOGIN).toBe('__LOGIN__');
    expect(SIGNALS.REFRESH).toBe('__REFRESH__');
    expect(SIGNALS.SETUP).toBe('__SETUP__');
    expect(SIGNALS.RESET_PASSWORD).toBe('__RESET_PASSWORD__');
    expect(SIGNALS.BACKUP_EXPORT).toBe('__BACKUP_EXPORT__');
    expect(SIGNALS.BACKUP_IMPORT).toBe('__BACKUP_IMPORT__');
    expect(SIGNALS.BACKUP_IMPORT_OVERWRITE).toBe('__BACKUP_IMPORT_OVERWRITE__');
    expect(SIGNALS.VIEW).toBe('__VIEW__');
  });
});

describe('parseSignal', () => {
  it('should extract payload from matching signal', () => {
    expect(parseSignal('__VIEW__agents', SIGNALS.VIEW)).toBe('agents');
    expect(parseSignal('__RESET_PASSWORD__admin', SIGNALS.RESET_PASSWORD)).toBe('admin');
    expect(parseSignal('__BACKUP_EXPORT__./backup.enc', SIGNALS.BACKUP_EXPORT)).toBe('./backup.enc');
  });

  it('should return empty string for signal with no payload', () => {
    expect(parseSignal('__CLEAR__', SIGNALS.CLEAR)).toBe('');
  });

  it('should return null for non-matching signal', () => {
    expect(parseSignal('__VIEW__agents', SIGNALS.CLEAR)).toBeNull();
    expect(parseSignal('not a signal', SIGNALS.VIEW)).toBeNull();
  });

  it('should handle BACKUP_IMPORT_OVERWRITE vs BACKUP_IMPORT correctly', () => {
    const content = '__BACKUP_IMPORT_OVERWRITE__./data.enc';
    expect(parseSignal(content, SIGNALS.BACKUP_IMPORT_OVERWRITE)).toBe('./data.enc');
    // BACKUP_IMPORT should NOT match BACKUP_IMPORT_OVERWRITE prefix
    expect(parseSignal(content, SIGNALS.BACKUP_IMPORT)).not.toBe('./data.enc');
  });
});

