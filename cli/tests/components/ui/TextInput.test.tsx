/**
 * Tests for TextInput component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';

// Store captured InkTextInput callbacks
let capturedOnChange: ((value: string) => void) | undefined;
let capturedOnSubmit: ((value: string) => void) | undefined;

// Mock ink-text-input to capture callbacks
vi.mock('ink-text-input', async () => {
  const { Text } = await import('ink');
  return {
    default: ({
      value,
      onChange,
      onSubmit,
      placeholder,
    }: {
      value: string;
      onChange: (value: string) => void;
      onSubmit: (value: string) => void;
      placeholder?: string;
    }) => {
      capturedOnChange = onChange;
      capturedOnSubmit = onSubmit;
      return React.createElement(Text, null, value || placeholder || '');
    },
  };
});

import { TextInput } from '../../../src/components/ui/TextInput.js';

describe('TextInput', () => {
  beforeEach(() => {
    capturedOnChange = undefined;
    capturedOnSubmit = undefined;
  });

  it('should render with label', () => {
    const { lastFrame } = render(
      <TextInput label="Username" onSubmit={vi.fn()} />
    );

    expect(lastFrame()).toContain('Username');
  });

  it('should show prompt indicator', () => {
    const { lastFrame } = render(
      <TextInput label="Test" onSubmit={vi.fn()} />
    );

    expect(lastFrame()).toContain('?');
  });

  it('should render with placeholder', () => {
    const { lastFrame } = render(
      <TextInput
        label="Name"
        onSubmit={vi.fn()}
        placeholder="Enter your name"
      />
    );

    expect(lastFrame()).toContain('Enter your name');
  });

  it('should render with default value', () => {
    const { lastFrame } = render(
      <TextInput
        label="Name"
        onSubmit={vi.fn()}
        defaultValue="John"
      />
    );

    expect(lastFrame()).toContain('John');
  });

  it('should accept validate prop', () => {
    const validate = vi.fn().mockReturnValue(null);
    const { lastFrame } = render(
      <TextInput label="Test" onSubmit={vi.fn()} validate={validate} />
    );

    expect(lastFrame()).toContain('Test');
  });

  it('should render without placeholder when not provided', () => {
    const { lastFrame } = render(
      <TextInput label="Name" onSubmit={vi.fn()} />
    );

    expect(lastFrame()).toContain('Name');
    expect(lastFrame()).toBeDefined();
  });

  describe('validation', () => {
    it('should show validation error when validate returns error', () => {
      const validate = vi.fn().mockReturnValue('Field is required');
      const onSubmit = vi.fn();

      const { lastFrame, rerender } = render(
        <TextInput label="Name" onSubmit={onSubmit} validate={validate} />
      );

      // Trigger submit with empty value
      capturedOnSubmit?.('');
      rerender(<TextInput label="Name" onSubmit={onSubmit} validate={validate} />);

      expect(lastFrame()).toContain('Field is required');
      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('should call onSubmit when validation passes', () => {
      const validate = vi.fn().mockReturnValue(null);
      const onSubmit = vi.fn();

      render(<TextInput label="Name" onSubmit={onSubmit} validate={validate} />);

      capturedOnSubmit?.('valid value');

      expect(validate).toHaveBeenCalledWith('valid value');
      expect(onSubmit).toHaveBeenCalledWith('valid value');
    });

    it('should call onSubmit when no validation is provided', () => {
      const onSubmit = vi.fn();

      render(<TextInput label="Name" onSubmit={onSubmit} />);

      capturedOnSubmit?.('test value');

      expect(onSubmit).toHaveBeenCalledWith('test value');
    });
  });

  describe('onChange', () => {
    it('should clear error when value changes', () => {
      const validate = vi.fn().mockReturnValue('Error message');
      const onSubmit = vi.fn();

      const { lastFrame, rerender } = render(
        <TextInput label="Name" onSubmit={onSubmit} validate={validate} />
      );

      // First trigger error
      capturedOnSubmit?.('');
      rerender(<TextInput label="Name" onSubmit={onSubmit} validate={validate} />);
      expect(lastFrame()).toContain('Error message');

      // Then change value to clear error
      capturedOnChange?.('new value');
      rerender(<TextInput label="Name" onSubmit={onSubmit} validate={validate} />);

      // Error should be cleared after change
      expect(lastFrame()).not.toContain('Error message');
    });

    it('should update internal value on change', () => {
      const onSubmit = vi.fn();

      const { lastFrame, rerender } = render(
        <TextInput label="Name" onSubmit={onSubmit} />
      );

      capturedOnChange?.('updated value');
      rerender(<TextInput label="Name" onSubmit={onSubmit} />);

      expect(lastFrame()).toContain('updated value');
    });
  });
});
