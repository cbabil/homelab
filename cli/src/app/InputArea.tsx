import { Box, Text, useInput } from 'ink';
import InkTextInput from 'ink-text-input';
import React, { useState, useCallback } from 'react';

interface InputAreaProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (value: string) => void;
  commandHistory: string[];
  historyIndex: number;
  onHistoryNavigate: (index: number) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function InputArea({
  value,
  onChange,
  onSubmit,
  commandHistory,
  historyIndex,
  onHistoryNavigate,
  disabled = false,
  placeholder = 'Type a command or /help',
}: InputAreaProps) {
  const [savedInput, setSavedInput] = useState('');

  const handleSubmit = useCallback(
    (val: string) => {
      if (disabled || !val.trim()) return;
      onSubmit(val.trim());
      setSavedInput('');
    },
    [disabled, onSubmit]
  );

  // Handle command history navigation
  useInput(
    (input, key) => {
      if (disabled) return;

      if (key.upArrow) {
        // Navigate backward in history
        if (commandHistory.length === 0) return;

        if (historyIndex === -1) {
          // Save current input before navigating
          setSavedInput(value);
          const newIndex = commandHistory.length - 1;
          onHistoryNavigate(newIndex);
          onChange(commandHistory[newIndex] || '');
        } else if (historyIndex > 0) {
          const newIndex = historyIndex - 1;
          onHistoryNavigate(newIndex);
          onChange(commandHistory[newIndex] || '');
        }
      } else if (key.downArrow) {
        // Navigate forward in history
        if (historyIndex === -1) return;

        if (historyIndex < commandHistory.length - 1) {
          const newIndex = historyIndex + 1;
          onHistoryNavigate(newIndex);
          onChange(commandHistory[newIndex] || '');
        } else {
          // Return to current input
          onHistoryNavigate(-1);
          onChange(savedInput);
        }
      } else if (key.ctrl && input === 'l') {
        // Ctrl+L - clear is handled by parent
      } else if (key.ctrl && input === 'c') {
        // Ctrl+C - cancel is handled by parent
        onChange('');
        onHistoryNavigate(-1);
        setSavedInput('');
      }
    },
    { isActive: !disabled }
  );

  return (
    <Box>
      <Text color="green" bold>
        {'> '}
      </Text>
      {disabled ? (
        <Text color="gray">{value || 'Processing...'}</Text>
      ) : (
        <InkTextInput
          value={value}
          onChange={onChange}
          onSubmit={handleSubmit}
          placeholder={placeholder}
        />
      )}
    </Box>
  );
}
