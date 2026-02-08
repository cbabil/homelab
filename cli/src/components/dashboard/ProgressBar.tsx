/**
 * Terminal-style progress bar component
 *
 * Renders: LABEL  [########-----]  65%
 */

import { Box, Text } from 'ink';
import React from 'react';
import { COLORS, PROGRESS_CHARS } from '../../app/theme.js';

interface ProgressBarProps {
  label: string;
  value: number;
  max: number;
  width?: number;
  suffix?: string;
}

export function ProgressBar({
  label,
  value,
  max,
  width = 20,
  suffix,
}: ProgressBarProps) {
  const safeMax = Math.max(max, 1);
  const ratio = Math.min(value / safeMax, 1);
  const percentage = Math.round(ratio * 100);
  const filledCount = Math.round(ratio * width);
  const emptyCount = width - filledCount;

  const filled = PROGRESS_CHARS.filled.repeat(filledCount);
  const empty = PROGRESS_CHARS.empty.repeat(emptyCount);

  return (
    <Box>
      <Text color={COLORS.primary}>{label.padEnd(12)}</Text>
      <Text color={COLORS.dim}>{'['}</Text>
      <Text color={COLORS.bright}>{filled}</Text>
      <Text color={COLORS.dim}>{empty}</Text>
      <Text color={COLORS.dim}>{']'}</Text>
      <Text color={COLORS.primary}>{`  ${String(percentage).padStart(3)}%`}</Text>
      {suffix ? <Text color={COLORS.dim}>{`  ${suffix}`}</Text> : null}
    </Box>
  );
}
