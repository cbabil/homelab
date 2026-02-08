/**
 * System status panel with progress bars for MCP, agents, servers
 */

import { Box, Text } from 'ink';
import React from 'react';
import { COLORS } from '../../app/theme.js';
import { Panel } from './Panel.js';
import { ProgressBar } from './ProgressBar.js';

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
    <Panel title="SYSTEM_STATUS">
      <Box flexDirection="column">
        <Box marginBottom={0}>
          <Text color={COLORS.primary}>{'MCP         '}</Text>
          <Text color={mcpConnected ? COLORS.bright : COLORS.error}>
            {mcpConnected ? '[ONLINE]' : '[OFFLINE]'}
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
            {`STALE: ${staleCount}  UPDATES: ${pendingUpdates}`}
          </Text>
        </Box>
      </Box>
    </Panel>
  );
}
