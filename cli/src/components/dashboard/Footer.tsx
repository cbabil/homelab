/**
 * Footer status line with version, MCP URL, and connection status
 */

import { Box, Text } from 'ink';
import React from 'react';
import { COLORS } from '../../app/theme.js';

interface FooterProps {
  version: string;
  mcpUrl: string;
  connectionStatus: 'connected' | 'connecting' | 'disconnected';
}

export function Footer({ version, mcpUrl, connectionStatus }: FooterProps) {
  const statusLabel = connectionStatus.charAt(0).toUpperCase() +
    connectionStatus.slice(1);

  const statusColor = connectionStatus === 'connected'
    ? COLORS.bright
    : connectionStatus === 'connecting'
      ? COLORS.dim
      : COLORS.error;

  return (
    <Box marginBottom={1}>
      <Text color={COLORS.dim}>
        {`VERSION: ${version}  MCP: ${mcpUrl}  STATUS: `}
      </Text>
      <Text color={statusColor}>{statusLabel}</Text>
    </Box>
  );
}
