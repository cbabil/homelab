/**
 * Tests for PasswordInput component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';

// Store captured InkTextInput callbacks
let capturedOnChange: ((value: string) => void) | undefined;
let capturedOnSubmit: ((value: string) => void) | undefined;
let capturedMask: string | undefined;

// Mock ink-text-input to capture callbacks
vi.mock('ink-text-input', async () => {
  const { Text } = await import('ink');
  return {
    default: ({
      value,
      onChange,
      onSubmit,
      mask,
    }: {
      value: string;
      onChange: (value: string) => void;
      onSubmit: (value: string) => void;
      mask?: string;
    }) => {
      capturedOnChange = onChange;
      capturedOnSubmit = onSubmit;
      capturedMask = mask;
      // Display masked value for testing
      const displayValue = mask ? value.replace(/./g, mask) : value;
      return React.createElement(Text, null, displayValue || '');
    },
  };
});

import { PasswordInput } from '../../../src/components/ui/PasswordInput.js';

describe('PasswordInput', () => {
  beforeEach(() => {
    capturedOnChange = undefined;
    capturedOnSubmit = undefined;
    capturedMask = undefined;
  });

  it('should render with label', () => {
    const { lastFrame } = render(
      <PasswordInput label="Password" onSubmit={vi.fn()} />
    );

    expect(lastFrame()).toContain('Password');
  });

  it('should show prompt indicator', () => {
    const { lastFrame } = render(
      <PasswordInput label="Test" onSubmit={vi.fn()} />
    );

    expect(lastFrame()).toContain('?');
  });

  it('should accept validate prop', () => {
    const validate = vi.fn().mockReturnValue(null);
    const { lastFrame } = render(
      <PasswordInput label="Password" onSubmit={vi.fn()} validate={validate} />
    );

    expect(lastFrame()).toContain('Password');
  });

  it('should render without error initially', () => {
    const { lastFrame } = render(
      <PasswordInput label="Password" onSubmit={vi.fn()} />
    );

    expect(lastFrame()).toBeDefined();
    expect(lastFrame()).not.toContain('Error');
  });

  it('should render label with colon', () => {
    const { lastFrame } = render(
      <PasswordInput label="Enter password" onSubmit={vi.fn()} />
    );

    expect(lastFrame()).toContain('Enter password:');
  });

  it('should use mask character for password', () => {
    render(<PasswordInput label="Password" onSubmit={vi.fn()} />);

    expect(capturedMask).toBe('*');
  });

  describe('validation', () => {
    it('should show validation error when validate returns error', () => {
      const validate = vi.fn().mockReturnValue('Password too short');
      const onSubmit = vi.fn();

      const { lastFrame, rerender } = render(
        <PasswordInput label="Password" onSubmit={onSubmit} validate={validate} />
      );

      // Trigger submit with short value
      capturedOnSubmit?.('123');
      rerender(
        <PasswordInput label="Password" onSubmit={onSubmit} validate={validate} />
      );

      expect(lastFrame()).toContain('Password too short');
      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('should call onSubmit when validation passes', () => {
      const validate = vi.fn().mockReturnValue(null);
      const onSubmit = vi.fn();

      render(
        <PasswordInput label="Password" onSubmit={onSubmit} validate={validate} />
      );

      capturedOnSubmit?.('validpassword');

      expect(validate).toHaveBeenCalledWith('validpassword');
      expect(onSubmit).toHaveBeenCalledWith('validpassword');
    });

    it('should call onSubmit when no validation is provided', () => {
      const onSubmit = vi.fn();

      render(<PasswordInput label="Password" onSubmit={onSubmit} />);

      capturedOnSubmit?.('secret');

      expect(onSubmit).toHaveBeenCalledWith('secret');
    });
  });

  describe('onChange', () => {
    it('should clear error when value changes', () => {
      const validate = vi.fn().mockReturnValue('Error message');
      const onSubmit = vi.fn();

      const { lastFrame, rerender } = render(
        <PasswordInput label="Password" onSubmit={onSubmit} validate={validate} />
      );

      // First trigger error
      capturedOnSubmit?.('short');
      rerender(
        <PasswordInput label="Password" onSubmit={onSubmit} validate={validate} />
      );
      expect(lastFrame()).toContain('Error message');

      // Then change value to clear error
      capturedOnChange?.('new password');
      rerender(
        <PasswordInput label="Password" onSubmit={onSubmit} validate={validate} />
      );

      // Error should be cleared after change
      expect(lastFrame()).not.toContain('Error message');
    });

    it('should update internal value on change', () => {
      const onSubmit = vi.fn();

      const { lastFrame, rerender } = render(
        <PasswordInput label="Password" onSubmit={onSubmit} />
      );

      capturedOnChange?.('test');
      rerender(<PasswordInput label="Password" onSubmit={onSubmit} />);

      // Value should be masked
      expect(lastFrame()).toContain('****');
    });
  });
});
