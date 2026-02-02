/**
 * Tests for Banner component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { Banner } from '../../../src/components/ui/Banner.js';

describe('Banner', () => {
  it('should render the banner', () => {
    const { lastFrame } = render(<Banner />);

    expect(lastFrame()).toBeDefined();
  });

  it('should contain Tomo text', () => {
    const { lastFrame } = render(<Banner />);

    expect(lastFrame()).toContain('Tomo');
  });

  it('should contain Admin CLI text', () => {
    const { lastFrame } = render(<Banner />);

    expect(lastFrame()).toContain('Admin CLI');
  });

  it('should have border characters', () => {
    const { lastFrame } = render(<Banner />);

    expect(lastFrame()).toContain('╔');
    expect(lastFrame()).toContain('╚');
    expect(lastFrame()).toContain('║');
  });
});
