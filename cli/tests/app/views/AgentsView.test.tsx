/**
 * Tests for AgentsView component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { AgentsView } from '../../../src/app/views/AgentsView.js';
import type { DashboardAgentInfo } from '../../../src/app/dashboard-types.js';

const mockAgents: DashboardAgentInfo[] = [
  { id: 'agent-001', server_id: 'srv-001', status: 'connected', version: '1.0.0', last_seen: '2025-01-01' },
  { id: 'agent-002', server_id: 'srv-002', status: 'disconnected', version: '0.9.0', last_seen: '2024-12-31' },
];

describe('AgentsView', () => {
  it('should render panel title', () => {
    const { lastFrame } = render(<AgentsView agents={mockAgents} />);
    expect(lastFrame()).toContain('[ AGENT_MANAGEMENT ]');
  });

  it('should render all column headers', () => {
    const { lastFrame } = render(<AgentsView agents={mockAgents} />);
    const frame = lastFrame() || '';
    expect(frame).toContain('ID');
    expect(frame).toContain('SERVER');
    expect(frame).toContain('STATUS');
    expect(frame).toContain('VERSION');
    expect(frame).toContain('LAST SEEN');
  });

  it('should render agent data', () => {
    const { lastFrame } = render(<AgentsView agents={mockAgents} />);
    const frame = lastFrame() || '';
    expect(frame).toContain('agent-001');
    expect(frame).toContain('srv-001');
  });

  it('should show status badges', () => {
    const { lastFrame } = render(<AgentsView agents={mockAgents} />);
    const frame = lastFrame() || '';
    expect(frame).toContain('[ACTIVE]');
    expect(frame).toContain('[OFFLINE]');
  });

  it('should show empty message when no agents', () => {
    const { lastFrame } = render(<AgentsView agents={[]} />);
    expect(lastFrame()).toContain('No agents registered');
  });
});
