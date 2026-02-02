/**
 * Tests for Spinner component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { Spinner } from '../../../src/components/ui/Spinner.js';

describe('Spinner', () => {
  it('should render with text', () => {
    const { lastFrame } = render(<Spinner text="Loading..." />);

    expect(lastFrame()).toContain('Loading...');
  });

  it('should render with different text', () => {
    const { lastFrame } = render(<Spinner text="Processing data" />);

    expect(lastFrame()).toContain('Processing data');
  });

  it('should render spinner animation character', () => {
    const { lastFrame } = render(<Spinner text="Test" />);

    // The spinner should render something
    expect(lastFrame()).toBeDefined();
    expect(lastFrame()!.length).toBeGreaterThan(0);
  });
});
