/**
 * Panel wrapper component with green monochrome border
 */

import { Box, Text } from 'ink';
import React from 'react';
import { COLORS, BORDER, formatPanelHeader } from '../../app/theme.js';

interface PanelProps {
  title: string;
  children: React.ReactNode;
  width?: number | string;
  height?: number;
}

export function Panel({ title, children, width, height }: PanelProps) {
  return (
    <Box
      flexDirection="column"
      borderStyle={BORDER.style}
      borderColor={BORDER.color}
      width={width}
      height={height}
      paddingX={1}
      flexGrow={1}
    >
      <Box marginBottom={1}>
        <Text bold color={COLORS.bright}>
          {formatPanelHeader(title)}
        </Text>
      </Box>
      {children}
    </Box>
  );
}
