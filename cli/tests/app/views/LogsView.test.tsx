/**
 * Tests for LogsView component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { LogsView } from '../../../src/app/views/LogsView.js';
import type { ActivityLogEntry } from '../../../src/components/dashboard/ActivityLog.js';

const mockEntries: ActivityLogEntry[] = [
  { id: '1', timestamp: new Date('2025-01-01T12:00:00'), type: 'CMD', message: '/help' },
  { id: '2', timestamp: new Date('2025-01-01T12:00:05'), type: 'OK', message: 'Help displayed' },
];

describe('LogsView', () => {
  it('should render activity log panel', () => {
    const { lastFrame } = render(<LogsView entries={mockEntries} />);
    expect(lastFrame()).toContain('[ RECENT_ACTIVITY ]');
  });

  it('should render log entries', () => {
    const { lastFrame } = render(<LogsView entries={mockEntries} />);
    const frame = lastFrame() || '';
    expect(frame).toContain('/help');
    expect(frame).toContain('Help displayed');
  });

  it('should show empty message when no entries', () => {
    const { lastFrame } = render(<LogsView entries={[]} />);
    expect(lastFrame()).toContain('No recent activity');
  });
});
