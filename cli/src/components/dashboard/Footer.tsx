/**
 * Footer status line with version, MCP URL, and connection status
 */

import { Box, Text } from 'ink';
import React from 'react';
import { COLORS } from '../../app/theme.js';
import { t } from '../../i18n/index.js';

interface FooterProps {
  version: string;
  mcpUrl: string;
  connectionStatus: 'connected' | 'connecting' | 'disconnected';
}

const STATUS_MAP: Record<string, string> = {
  connected: 'common.connected',
  connecting: 'common.connecting',
  disconnected: 'common.disconnected',
};

export function Footer({ version, mcpUrl, connectionStatus }: FooterProps) {
  const statusLabel = t(STATUS_MAP[connectionStatus] || 'common.disconnected');

  const statusColor = connectionStatus === 'connected'
    ? COLORS.bright
    : connectionStatus === 'connecting'
      ? COLORS.dim
      : COLORS.error;

  return (
    <Box marginBottom={1}>
      <Text color={COLORS.dim}>
        {`${t('common.version')}: ${version}  ${t('common.mcp')}: ${mcpUrl}  ${t('common.status')}: `}
      </Text>
      <Text color={statusColor}>{statusLabel}</Text>
    </Box>
  );
}
