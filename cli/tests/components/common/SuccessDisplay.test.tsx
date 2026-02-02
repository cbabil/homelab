/**
 * Tests for SuccessDisplay component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { SuccessDisplay } from '../../../src/components/common/SuccessDisplay.js';

describe('SuccessDisplay', () => {
  it('should render success message', () => {
    const { lastFrame } = render(<SuccessDisplay message="Operation completed" />);

    expect(lastFrame()).toContain('Operation completed');
  });

  it('should show success symbol', () => {
    const { lastFrame } = render(<SuccessDisplay message="Test" />);

    expect(lastFrame()).toContain('✔');
  });

  it('should render with details when provided', () => {
    const { lastFrame } = render(
      <SuccessDisplay
        message="User created"
        details={{ Username: 'admin', Role: 'administrator' }}
      />
    );

    expect(lastFrame()).toContain('User created');
    expect(lastFrame()).toContain('Username');
    expect(lastFrame()).toContain('admin');
    expect(lastFrame()).toContain('Role');
    expect(lastFrame()).toContain('administrator');
  });

  it('should not show details when not provided', () => {
    const { lastFrame } = render(<SuccessDisplay message="Success!" />);

    expect(lastFrame()).toContain('Success!');
    expect(lastFrame()).toBeDefined();
  });

  it('should handle empty details object', () => {
    const { lastFrame } = render(
      <SuccessDisplay message="Done" details={{}} />
    );

    expect(lastFrame()).toContain('Done');
  });

  it('should handle multiple details', () => {
    const { lastFrame } = render(
      <SuccessDisplay
        message="Backup created"
        details={{
          File: 'backup.enc',
          Size: '1.2 MB',
          Created: '2024-01-15',
        }}
      />
    );

    expect(lastFrame()).toContain('File');
    expect(lastFrame()).toContain('backup.enc');
    expect(lastFrame()).toContain('Size');
    expect(lastFrame()).toContain('1.2 MB');
    expect(lastFrame()).toContain('Created');
  });
});
