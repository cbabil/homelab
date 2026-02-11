/**
 * System status panel with progress bars for MCP, agents, servers
 */

import { Box, Text } from 'ink';
import React from 'react';
import { COLORS } from '../../app/theme.js';
import { Panel } from './Panel.js';
import { ProgressBar } from './ProgressBar.js';
import { t } from '../../i18n/index.js';

interface SystemStatusPanelProps {
  mcpConnected: boolean;
  agentCount: number;
  totalAgents: number;
  serverCount: number;
  totalServers: number;
  staleCount?: number;
  pendingUpdates?: number;
}

export function SystemStatusPanel({
  mcpConnected,
  agentCount,
  totalAgents,
  serverCount,
  totalServers,
  staleCount = 0,
  pendingUpdates = 0,
}: SystemStatusPanelProps) {
  return (
    <Panel title={t('dashboard.systemStatus')}>
      <Box flexDirection="column">
        <Box marginBottom={0}>
          <Text color={COLORS.primary}>{`${t('common.mcp')}         `}</Text>
          <Text color={mcpConnected ? COLORS.bright : COLORS.error}>
            {mcpConnected ? `[${t('common.online')}]` : `[${t('common.offline')}]`}
          </Text>
        </Box>
        <ProgressBar
          label="AGENTS"
          value={agentCount}
          max={Math.max(totalAgents, 1)}
          suffix={`${agentCount}/${totalAgents}`}
        />
        <ProgressBar
          label="SERVERS"
          value={serverCount}
          max={Math.max(totalServers, 1)}
          suffix={`${serverCount}/${totalServers}`}
        />
        <Box marginTop={1}>
          <Text color={COLORS.dim}>
            {`${t('dashboard.staleLabel', { count: staleCount })}  ${t('dashboard.updatesLabel', { count: pendingUpdates })}`}
          </Text>
        </Box>
      </Box>
    </Panel>
  );
}
