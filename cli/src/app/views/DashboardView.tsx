/**
 * Main dashboard view with system status and active agents
 */

import { Box } from 'ink';
import React from 'react';
import { SystemStatusPanel } from '../../components/dashboard/SystemStatusPanel.js';
import { ActiveAgentsPanel } from '../../components/dashboard/ActiveAgentsPanel.js';
import { ActiveServersPanel } from '../../components/dashboard/ActiveServersPanel.js';
import { ActivityLog } from '../../components/dashboard/ActivityLog.js';
import type { ActivityEntry, DashboardData } from '../dashboard-types.js';

interface DashboardViewProps {
  data: DashboardData;
  activityLog: ActivityEntry[];
  mcpConnected: boolean;
}

export function DashboardView({
  data,
  activityLog,
  mcpConnected,
}: DashboardViewProps) {
  const onlineAgents = data.agents.filter(
    (a) => a.status === 'connected'
  ).length;
  const onlineServers = data.servers.filter(
    (s) => s.status === 'online'
  ).length;

  const agentRows = data.agents.map((a) => ({
    id: a.id,
    server_id: a.server_id,
    status: a.status,
  }));

  const serverRows = data.servers.map((s) => ({
    id: s.id,
    name: s.name,
    hostname: s.hostname,
    status: s.status,
  }));

  return (
    <Box flexDirection="column" flexGrow={1}>
      {/* Top row: System status (left) + Agents & Servers side-by-side (right) */}
      <Box>
        <Box width="34%">
          <SystemStatusPanel
            mcpConnected={mcpConnected}
            agentCount={onlineAgents}
            totalAgents={data.agents.length}
            serverCount={onlineServers}
            totalServers={data.servers.length}
          />
        </Box>
        <Box width="33%">
          <ActiveAgentsPanel agents={agentRows} />
        </Box>
        <Box width="33%">
          <ActiveServersPanel servers={serverRows} />
        </Box>
      </Box>

      {/* Activity log */}
      <ActivityLog entries={activityLog} height={14} />
    </Box>
  );
}
