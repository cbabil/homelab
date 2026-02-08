/**
 * Tests for SystemStatusPanel component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { SystemStatusPanel } from '../../../src/components/dashboard/SystemStatusPanel.js';

describe('SystemStatusPanel', () => {
  it('should render panel title', () => {
    const { lastFrame } = render(
      <SystemStatusPanel
        mcpConnected={true}
        agentCount={3}
        totalAgents={5}
        serverCount={2}
        totalServers={3}
      />
    );

    expect(lastFrame()).toContain('[ SYSTEM_STATUS ]');
  });

  it('should show MCP online when connected', () => {
    const { lastFrame } = render(
      <SystemStatusPanel
        mcpConnected={true}
        agentCount={3}
        totalAgents={5}
        serverCount={2}
        totalServers={3}
      />
    );

    expect(lastFrame()).toContain('[ONLINE]');
  });

  it('should show MCP offline when disconnected', () => {
    const { lastFrame } = render(
      <SystemStatusPanel
        mcpConnected={false}
        agentCount={0}
        totalAgents={0}
        serverCount={0}
        totalServers={0}
      />
    );

    expect(lastFrame()).toContain('[OFFLINE]');
  });

  it('should render agent progress bar', () => {
    const { lastFrame } = render(
      <SystemStatusPanel
        mcpConnected={true}
        agentCount={3}
        totalAgents={5}
        serverCount={2}
        totalServers={3}
      />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('AGENTS');
    expect(frame).toContain('3/5');
  });

  it('should render server progress bar', () => {
    const { lastFrame } = render(
      <SystemStatusPanel
        mcpConnected={true}
        agentCount={3}
        totalAgents={5}
        serverCount={2}
        totalServers={3}
      />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('SERVERS');
    expect(frame).toContain('2/3');
  });

  it('should show stale and update counts', () => {
    const { lastFrame } = render(
      <SystemStatusPanel
        mcpConnected={true}
        agentCount={3}
        totalAgents={5}
        serverCount={2}
        totalServers={3}
        staleCount={1}
        pendingUpdates={2}
      />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('STALE: 1');
    expect(frame).toContain('UPDATES: 2');
  });

  it('should default stale and updates to zero', () => {
    const { lastFrame } = render(
      <SystemStatusPanel
        mcpConnected={true}
        agentCount={0}
        totalAgents={0}
        serverCount={0}
        totalServers={0}
      />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('STALE: 0');
    expect(frame).toContain('UPDATES: 0');
  });
});
