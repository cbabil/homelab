/**
 * Active agents panel with a DataTable showing agent info
 */

import React from 'react';
import { Panel } from './Panel.js';
import { DataTable, type DataColumn } from './DataTable.js';
import { StatusBadge } from './StatusBadge.js';
import type { BadgeStatus } from '../../app/theme.js';

export interface AgentRow {
  id: string;
  server_id: string;
  status: string;
}

function mapAgentStatus(status: string): BadgeStatus {
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

const AGENT_COLUMNS: DataColumn<AgentRow>[] = [
  { key: 'id', header: 'ID', width: 14 },
  { key: 'server_id', header: 'Server', width: 14 },
  {
    key: 'status',
    header: 'Status',
    width: 12,
    render: (row: AgentRow) => (
      <StatusBadge status={mapAgentStatus(row.status)} />
    ),
  },
];

interface ActiveAgentsPanelProps {
  agents: AgentRow[];
}

export function ActiveAgentsPanel({ agents }: ActiveAgentsPanelProps) {
  return (
    <Panel title="ACTIVE_AGENTS">
      <DataTable
        columns={AGENT_COLUMNS}
        data={agents}
        emptyMessage="No agents registered"
      />
    </Panel>
  );
}
