/**
 * Tests for dashboard types and helpers.
 */

import { describe, it, expect } from 'vitest';
import {
  createActivityEntry,
  NAV_ITEMS,
  type ViewMode,
  type ActivityEntry,
} from '../../src/app/dashboard-types.js';

describe('dashboard-types', () => {
  describe('createActivityEntry', () => {
    it('should create an activity entry with correct type', () => {
      const entry = createActivityEntry('CMD', 'test command');
      expect(entry.type).toBe('CMD');
      expect(entry.message).toBe('test command');
    });

    it('should generate unique IDs', () => {
      const entry1 = createActivityEntry('OK', 'success');
      const entry2 = createActivityEntry('ERR', 'failure');
      expect(entry1.id).not.toBe(entry2.id);
    });

    it('should include a timestamp', () => {
      const before = new Date();
      const entry = createActivityEntry('SYS', 'system event');
      const after = new Date();

      expect(entry.timestamp.getTime()).toBeGreaterThanOrEqual(before.getTime());
      expect(entry.timestamp.getTime()).toBeLessThanOrEqual(after.getTime());
    });

    it('should support all entry types', () => {
      const types: ActivityEntry['type'][] = ['CMD', 'OK', 'ERR', 'WARN', 'SYS'];
      for (const type of types) {
        const entry = createActivityEntry(type, 'msg');
        expect(entry.type).toBe(type);
      }
    });
  });

  describe('NAV_ITEMS', () => {
    it('should have 4 navigation items', () => {
      expect(NAV_ITEMS).toHaveLength(4);
    });

    it('should include dashboard as first item', () => {
      expect(NAV_ITEMS[0]!.key).toBe('dashboard');
      expect(NAV_ITEMS[0]!.label).toBe('dashboard');
    });

    it('should include all views', () => {
      const keys = NAV_ITEMS.map((item) => item.key);
      expect(keys).toContain('dashboard');
      expect(keys).toContain('agents');
      expect(keys).toContain('logs');
      expect(keys).toContain('settings');
    });
  });

  describe('ViewMode type', () => {
    it('should accept valid view modes', () => {
      const modes: ViewMode[] = ['dashboard', 'agents', 'logs', 'settings'];
      expect(modes).toHaveLength(4);
    });
  });
});
