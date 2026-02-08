/**
 * Tests for NavBar component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { NavBar, type NavItem } from '../../../src/components/dashboard/NavBar.js';

const testItems: NavItem[] = [
  { key: 'dashboard', label: 'dashboard' },
  { key: 'agents', label: 'agents' },
  { key: 'logs', label: 'logs' },
  { key: 'settings', label: 'settings' },
];

describe('NavBar', () => {
  it('should render tab labels in uppercase', () => {
    const { lastFrame } = render(
      <NavBar items={testItems} activeTab="dashboard" />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('DASHBOARD');
    expect(frame).toContain('AGENTS');
    expect(frame).toContain('LOGS');
    expect(frame).toContain('SETTINGS');
  });

  it('should show pipe separators between tabs', () => {
    const { lastFrame } = render(
      <NavBar items={testItems} activeTab="dashboard" />
    );

    expect(lastFrame()).toContain('\u2502');
  });

  it('should center tabs', () => {
    const { lastFrame } = render(
      <NavBar items={testItems} activeTab="agents" />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('DASHBOARD');
    expect(frame).toContain('AGENTS');
  });
});
