/**
 * Full agent management view with detailed table
 */

import React from 'react';
import { Panel } from '../../components/dashboard/Panel.js';
import { DataTable, type DataColumn } from '../../components/dashboard/DataTable.js';
import { StatusBadge } from '../../components/dashboard/StatusBadge.js';
import type { BadgeStatus } from '../theme.js';
import type { DashboardAgentInfo } from '../dashboard-types.js';

function mapAgentBadge(status: string): BadgeStatus {
  switch (status) {
    case 'connected':
      return 'active';
    case 'disconnected':
      return 'offline';
    case 'locked':
      return 'locked';
    default:
      return 'idle';
  }
}

const AGENT_COLUMNS: DataColumn<DashboardAgentInfo>[] = [
  { key: 'id', header: 'ID', width: 14 },
  { key: 'server_id', header: 'Server', width: 14 },
  {
    key: 'status',
    header: 'Status',
    width: 12,
    render: (row) => <StatusBadge status={mapAgentBadge(row.status)} />,
  },
  { key: 'version', header: 'Version', width: 10 },
  { key: 'last_seen', header: 'Last Seen', width: 20 },
];

interface AgentsViewProps {
  agents: DashboardAgentInfo[];
}

export function AgentsView({ agents }: AgentsViewProps) {
  return (
    <Panel title="AGENT_MANAGEMENT">
      <DataTable
        columns={AGENT_COLUMNS}
        data={agents}
        emptyMessage="No agents registered"
      />
    </Panel>
  );
}
