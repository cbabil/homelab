/**
 * Tests for ActiveAgentsPanel component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { ActiveAgentsPanel, type AgentRow } from '../../../src/components/dashboard/ActiveAgentsPanel.js';

const testAgents: AgentRow[] = [
  { id: 'agent-001', server_id: 'srv-001', status: 'connected' },
  { id: 'agent-002', server_id: 'srv-002', status: 'disconnected' },
];

describe('ActiveAgentsPanel', () => {
  it('should render panel title', () => {
    const { lastFrame } = render(
      <ActiveAgentsPanel agents={testAgents} />
    );

    expect(lastFrame()).toContain('[ ACTIVE_AGENTS ]');
  });

  it('should render column headers', () => {
    const { lastFrame } = render(
      <ActiveAgentsPanel agents={testAgents} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('ID');
    expect(frame).toContain('SERVER');
    expect(frame).toContain('STATUS');
  });

  it('should render agent data', () => {
    const { lastFrame } = render(
      <ActiveAgentsPanel agents={testAgents} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('agent-001');
    expect(frame).toContain('srv-001');
  });

  it('should render status badges', () => {
    const { lastFrame } = render(
      <ActiveAgentsPanel agents={testAgents} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('[ACTIVE]');
    expect(frame).toContain('[OFFLINE]');
  });

  it('should show empty message when no agents', () => {
    const { lastFrame } = render(
      <ActiveAgentsPanel agents={[]} />
    );

    expect(lastFrame()).toContain('No agents registered');
  });
});
