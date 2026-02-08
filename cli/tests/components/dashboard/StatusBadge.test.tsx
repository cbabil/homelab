/**
 * Tests for StatusBadge component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { StatusBadge } from '../../../src/components/dashboard/StatusBadge.js';

describe('StatusBadge', () => {
  it('should render active badge', () => {
    const { lastFrame } = render(<StatusBadge status="active" />);
    expect(lastFrame()).toContain('[ACTIVE]');
  });

  it('should render idle badge', () => {
    const { lastFrame } = render(<StatusBadge status="idle" />);
    expect(lastFrame()).toContain('[IDLE]');
  });

  it('should render offline badge', () => {
    const { lastFrame } = render(<StatusBadge status="offline" />);
    expect(lastFrame()).toContain('[OFFLINE]');
  });

  it('should render locked badge', () => {
    const { lastFrame } = render(<StatusBadge status="locked" />);
    expect(lastFrame()).toContain('[LOCKED]');
  });
});
