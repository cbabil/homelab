/**
 * Tests for ActivityLog component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';

let capturedUseInputCallback:
  | ((input: string, key: Record<string, boolean>) => void)
  | undefined;

vi.mock('ink', async () => {
  const actual = await vi.importActual<typeof import('ink')>('ink');
  return {
    ...actual,
    useInput: (
      callback: (input: string, key: Record<string, boolean>) => void
    ) => {
      capturedUseInputCallback = callback;
    },
  };
});

import { ActivityLog, type ActivityLogEntry } from '../../../src/components/dashboard/ActivityLog.js';

const testEntries: ActivityLogEntry[] = [
  { id: '1', timestamp: new Date('2025-01-01T10:30:00'), type: 'CMD', message: 'agent list' },
  { id: '2', timestamp: new Date('2025-01-01T10:30:05'), type: 'OK', message: 'Fetched 3 agents' },
  { id: '3', timestamp: new Date('2025-01-01T10:31:00'), type: 'ERR', message: 'Connection timeout' },
];

describe('ActivityLog', () => {
  it('should render panel title', () => {
    const { lastFrame } = render(
      <ActivityLog entries={testEntries} />
    );

    expect(lastFrame()).toContain('RECENT_ACTIVITY');
  });

  it('should render log entries', () => {
    const { lastFrame } = render(
      <ActivityLog entries={testEntries} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('agent list');
    expect(frame).toContain('Fetched 3 agents');
    expect(frame).toContain('Connection timeout');
  });

  it('should render timestamps', () => {
    const { lastFrame } = render(
      <ActivityLog entries={testEntries} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('10:30:00');
  });

  it('should render entry types', () => {
    const { lastFrame } = render(
      <ActivityLog entries={testEntries} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('CMD');
    expect(frame).toContain('OK');
    expect(frame).toContain('ERR');
  });

  it('should show empty message when no entries', () => {
    const { lastFrame } = render(
      <ActivityLog entries={[]} />
    );

    expect(lastFrame()).toContain('No recent activity');
  });

  it('should auto-scroll to show latest entries', () => {
    const manyEntries: ActivityLogEntry[] = Array.from({ length: 30 }, (_, i) => ({
      id: String(i),
      timestamp: new Date('2025-01-01T10:00:00'),
      type: 'SYS' as const,
      message: `Entry ${i}`,
    }));

    const { lastFrame } = render(
      <ActivityLog entries={manyEntries} height={5} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('Entry 29');
    expect(frame).not.toContain('Entry 0');
  });

  it('should accept custom height', () => {
    const { lastFrame } = render(
      <ActivityLog entries={testEntries} height={10} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('agent list');
  });

  it('should register keyboard input handler', () => {
    const manyEntries: ActivityLogEntry[] = Array.from({ length: 30 }, (_, i) => ({
      id: String(i),
      timestamp: new Date('2025-01-01T10:00:00'),
      type: 'SYS' as const,
      message: `Entry ${i}`,
    }));

    render(<ActivityLog entries={manyEntries} height={5} />);

    expect(capturedUseInputCallback).toBeDefined();
  });

  it('should show scrollbar when content overflows', () => {
    const manyEntries: ActivityLogEntry[] = Array.from({ length: 30 }, (_, i) => ({
      id: String(i),
      timestamp: new Date('2025-01-01T10:00:00'),
      type: 'SYS' as const,
      message: `Entry ${i}`,
    }));

    const { lastFrame } = render(
      <ActivityLog entries={manyEntries} height={5} />
    );

    const frame = lastFrame() || '';
    // Scrollbar uses █ (thumb) and │ (track)
    expect(frame).toContain('\u2588');
    expect(frame).toContain('\u2502');
  });

  it('should not show scrollbar when content fits', () => {
    const { lastFrame } = render(
      <ActivityLog entries={testEntries} height={10} />
    );

    const frame = lastFrame() || '';
    // No scrollbar track character outside the panel border
    const lines = frame.split('\n');
    const contentLines = lines.filter((l) => l.includes('CMD') || l.includes('OK') || l.includes('ERR'));
    for (const line of contentLines) {
      // The │ in content lines should only be the panel border, not a track
      const stripped = line.replace(/^[^│]*│/, '').replace(/│[^│]*$/, '');
      expect(stripped).not.toContain('\u2588');
    }
  });
});
