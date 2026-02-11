/**
 * Hacker-style command prompt with history navigation
 */

import { Box, Text, useInput } from 'ink';
import InkTextInput from 'ink-text-input';
import React, { useState, useCallback } from 'react';
import { COLORS, formatPrompt } from '../../app/theme.js';
import { t } from '../../i18n/index.js';

interface CommandPromptProps {
  username: string;
  value: string;
  onChange: (value: string) => void;
  onSubmit: (value: string) => void;
  commandHistory: string[];
  historyIndex: number;
  onHistoryNavigate: (index: number) => void;
  disabled?: boolean;
  promptLabel?: string;
  mask?: boolean;
  offline?: boolean;
}

export function CommandPrompt({
  username,
  value,
  onChange,
  onSubmit,
  commandHistory,
  historyIndex,
  onHistoryNavigate,
  disabled = false,
  promptLabel,
  mask = false,
  offline = false,
}: CommandPromptProps) {
  const [savedInput, setSavedInput] = useState('');

  const handleSubmit = useCallback(
    (val: string) => {
      if (disabled) return;
      if (!promptLabel && !val.trim()) return;
      onSubmit(val.trim());
      setSavedInput('');
    },
    [disabled, onSubmit, promptLabel]
  );

  useInput(
    (_input, key) => {
      if (disabled) return;

      if (key.upArrow) {
        if (commandHistory.length === 0) return;
        if (historyIndex === -1) {
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
        if (historyIndex === -1) return;
        if (historyIndex < commandHistory.length - 1) {
          const newIndex = historyIndex + 1;
          onHistoryNavigate(newIndex);
          onChange(commandHistory[newIndex] || '');
        } else {
          onHistoryNavigate(-1);
          onChange(savedInput);
        }
      }
    },
    { isActive: !disabled }
  );

  const showOfflineBadge = offline && !promptLabel;
  const prompt = promptLabel
    || (showOfflineBadge ? 'tomo:~$ ' : formatPrompt(username, 'tomo'));

  return (
    <Box>
      {showOfflineBadge ? (
        <Text bold color={COLORS.error}>{`[ ${t('common.offline')} ] `}</Text>
      ) : null}
      <Text bold color={COLORS.bright}>
        {prompt}
      </Text>
      {disabled ? (
        <Text color={COLORS.dim}>{value || t('common.processing')}</Text>
      ) : (
        <InkTextInput
          value={value}
          onChange={onChange}
          onSubmit={handleSubmit}
          placeholder={promptLabel ? '' : t('common.typeCommandOrHelp')}
          mask={mask ? '*' : undefined}
        />
      )}
    </Box>
  );
}
