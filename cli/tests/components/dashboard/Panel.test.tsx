/**
 * Tests for Panel component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { Text } from 'ink';
import { Panel } from '../../../src/components/dashboard/Panel.js';

describe('Panel', () => {
  it('should render with a title', () => {
    const { lastFrame } = render(
      <Panel title="test">
        <Text>content</Text>
      </Panel>
    );

    expect(lastFrame()).toContain('[ TEST ]');
  });

  it('should render children', () => {
    const { lastFrame } = render(
      <Panel title="section">
        <Text>child content</Text>
      </Panel>
    );

    expect(lastFrame()).toContain('child content');
  });

  it('should have border characters', () => {
    const { lastFrame } = render(
      <Panel title="bordered">
        <Text>inside</Text>
      </Panel>
    );

    const frame = lastFrame() || '';
    // single border style uses these characters
    expect(frame).toContain('│');
  });

  it('should uppercase the title', () => {
    const { lastFrame } = render(
      <Panel title="lowercase title">
        <Text>body</Text>
      </Panel>
    );

    expect(lastFrame()).toContain('[ LOWERCASE TITLE ]');
  });
});
