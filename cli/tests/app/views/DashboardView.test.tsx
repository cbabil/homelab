/**
 * Tests for DashboardView component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { DashboardView } from '../../../src/app/views/DashboardView.js';
import type { DashboardData } from '../../../src/app/dashboard-types.js';
import type { ActivityLogEntry } from '../../../src/components/dashboard/ActivityLog.js';

const mockData: DashboardData = {
  agents: [
    { id: 'agent-001', server_id: 'srv-001', status: 'connected', version: '1.0', last_seen: null },
    { id: 'agent-002', server_id: 'srv-002', status: 'disconnected', version: '0.9', last_seen: null },
  ],
  servers: [
    { id: 'srv-001', name: 'Web', hostname: 'web.local', status: 'online' },
    { id: 'srv-002', name: 'DB', hostname: 'db.local', status: 'offline' },
  ],
  loading: false,
  error: null,
  lastRefresh: new Date(),
};

const mockActivityLog: ActivityLogEntry[] = [
  { id: '1', timestamp: new Date(), type: 'SYS', message: 'System initialized' },
];

describe('DashboardView', () => {
  it('should render system status panel', () => {
    const { lastFrame } = render(
      <DashboardView data={mockData} activityLog={mockActivityLog} mcpConnected={true} />
    );

    expect(lastFrame()).toContain('[ SYSTEM_STATUS ]');
  });

  it('should render active agents panel', () => {
    const { lastFrame } = render(
      <DashboardView data={mockData} activityLog={mockActivityLog} mcpConnected={true} />
    );

    expect(lastFrame()).toContain('[ ACTIVE_AGENTS ]');
  });

  it('should render active servers panel', () => {
    const { lastFrame } = render(
      <DashboardView data={mockData} activityLog={mockActivityLog} mcpConnected={true} />
    );

    expect(lastFrame()).toContain('[ ACTIVE_SERVERS ]');
  });

  it('should show server data', () => {
    const { lastFrame } = render(
      <DashboardView data={mockData} activityLog={mockActivityLog} mcpConnected={true} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('srv-001');
    expect(frame).toContain('Web');
  });

  it('should render activity log', () => {
    const { lastFrame } = render(
      <DashboardView data={mockData} activityLog={mockActivityLog} mcpConnected={true} />
    );

    expect(lastFrame()).toContain('[ RECENT_ACTIVITY ]');
  });

  it('should show agent data', () => {
    const { lastFrame } = render(
      <DashboardView data={mockData} activityLog={mockActivityLog} mcpConnected={true} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('agent-001');
  });

  it('should handle empty data', () => {
    const emptyData: DashboardData = {
      agents: [],
      servers: [],
      loading: false,
      error: null,
      lastRefresh: null,
    };

    const { lastFrame } = render(
      <DashboardView data={emptyData} activityLog={[]} mcpConnected={false} />
    );

    expect(lastFrame()).toContain('[ SYSTEM_STATUS ]');
    expect(lastFrame()).toContain('No agents registered');
  });
});
