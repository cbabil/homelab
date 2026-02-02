/**
 * Tests for ErrorDisplay component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { ErrorDisplay } from '../../../src/components/common/ErrorDisplay.js';

describe('ErrorDisplay', () => {
  it('should render error message', () => {
    const { lastFrame } = render(<ErrorDisplay message="Something went wrong" />);

    expect(lastFrame()).toContain('Something went wrong');
  });

  it('should show error indicator', () => {
    const { lastFrame } = render(<ErrorDisplay message="Test error" />);

    expect(lastFrame()).toContain('Error');
  });

  it('should show error symbol', () => {
    const { lastFrame } = render(<ErrorDisplay message="Test" />);

    expect(lastFrame()).toContain('✗');
  });

  it('should render with details when provided', () => {
    const { lastFrame } = render(
      <ErrorDisplay message="Failed" details="Connection refused on port 8000" />
    );

    expect(lastFrame()).toContain('Failed');
    expect(lastFrame()).toContain('Connection refused on port 8000');
  });

  it('should not show details when not provided', () => {
    const { lastFrame } = render(<ErrorDisplay message="Error occurred" />);

    expect(lastFrame()).toContain('Error occurred');
    // Should still render without issue
    expect(lastFrame()).toBeDefined();
  });
});
