/**
 * Tests for ActiveServersPanel component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { ActiveServersPanel, type ServerRow } from '../../../src/components/dashboard/ActiveServersPanel.js';

const testServers: ServerRow[] = [
  { id: 'srv-001', name: 'Web Server', hostname: 'web.local', status: 'online' },
  { id: 'srv-002', name: 'DB Server', hostname: 'db.local', status: 'offline' },
];

describe('ActiveServersPanel', () => {
  it('should render panel title', () => {
    const { lastFrame } = render(
      <ActiveServersPanel servers={testServers} />
    );

    expect(lastFrame()).toContain('[ ACTIVE_SERVERS ]');
  });

  it('should render column headers', () => {
    const { lastFrame } = render(
      <ActiveServersPanel servers={testServers} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('ID');
    expect(frame).toContain('NAME');
    expect(frame).toContain('HOSTNAME');
    expect(frame).toContain('STATUS');
  });

  it('should render server data', () => {
    const { lastFrame } = render(
      <ActiveServersPanel servers={testServers} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('srv-001');
    expect(frame).toContain('Web Server');
    expect(frame).toContain('web.local');
  });

  it('should render status badges', () => {
    const { lastFrame } = render(
      <ActiveServersPanel servers={testServers} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('[ACTIVE]');
    expect(frame).toContain('[OFFLINE]');
  });

  it('should show empty message when no servers', () => {
    const { lastFrame } = render(
      <ActiveServersPanel servers={[]} />
    );

    expect(lastFrame()).toContain('No servers registered');
  });
});
