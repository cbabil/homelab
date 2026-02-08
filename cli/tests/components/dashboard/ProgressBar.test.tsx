/**
 * Tests for ProgressBar component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { ProgressBar } from '../../../src/components/dashboard/ProgressBar.js';

describe('ProgressBar', () => {
  it('should render label', () => {
    const { lastFrame } = render(
      <ProgressBar label="CPU" value={50} max={100} />
    );

    expect(lastFrame()).toContain('CPU');
  });

  it('should show percentage', () => {
    const { lastFrame } = render(
      <ProgressBar label="MEM" value={75} max={100} />
    );

    expect(lastFrame()).toContain('75%');
  });

  it('should show 0% for zero value', () => {
    const { lastFrame } = render(
      <ProgressBar label="DISK" value={0} max={100} />
    );

    expect(lastFrame()).toContain('0%');
  });

  it('should show 100% for full value', () => {
    const { lastFrame } = render(
      <ProgressBar label="NET" value={100} max={100} />
    );

    expect(lastFrame()).toContain('100%');
  });

  it('should cap at 100% when value exceeds max', () => {
    const { lastFrame } = render(
      <ProgressBar label="OVER" value={200} max={100} />
    );

    expect(lastFrame()).toContain('100%');
  });

  it('should render filled and empty characters', () => {
    const { lastFrame } = render(
      <ProgressBar label="BAR" value={50} max={100} width={10} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('#');
    expect(frame).toContain('-');
  });

  it('should render suffix when provided', () => {
    const { lastFrame } = render(
      <ProgressBar label="RAM" value={4} max={8} suffix="4/8 GB" />
    );

    expect(lastFrame()).toContain('4/8 GB');
  });

  it('should handle zero max gracefully', () => {
    const { lastFrame } = render(
      <ProgressBar label="ZERO" value={0} max={0} />
    );

    expect(lastFrame()).toContain('0%');
  });
});
