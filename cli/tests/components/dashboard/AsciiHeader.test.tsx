/**
 * Tests for AsciiHeader component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { AsciiHeader } from '../../../src/components/dashboard/AsciiHeader.js';

describe('AsciiHeader', () => {
  it('should render ASCII art', () => {
    const { lastFrame } = render(<AsciiHeader />);
    expect(lastFrame()).toBeDefined();
  });

  it('should contain ADMIN text', () => {
    const { lastFrame } = render(<AsciiHeader />);
    expect(lastFrame()).toContain('A D M I N');
  });

  it('should contain block characters', () => {
    const { lastFrame } = render(<AsciiHeader />);
    const frame = lastFrame() || '';
    expect(frame).toContain('█');
  });
});
