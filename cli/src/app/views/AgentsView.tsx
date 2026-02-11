/**
 * Full agent management view with detailed table
 */

import React from 'react';
import { Panel } from '../../components/dashboard/Panel.js';
import { DataTable, type DataColumn } from '../../components/dashboard/DataTable.js';
import { StatusBadge } from '../../components/dashboard/StatusBadge.js';
import type { BadgeStatus } from '../theme.js';
import type { DashboardAgentInfo } from '../dashboard-types.js';
import { t } from '../../i18n/index.js';

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
  { key: 'id', header: t('agents.columnId'), width: 14 },
  { key: 'server_id', header: t('agents.columnServer'), width: 14 },
  {
    key: 'status',
    header: t('agents.columnStatus'),
    width: 12,
    render: (row) => <StatusBadge status={mapAgentBadge(row.status)} />,
  },
  { key: 'version', header: t('agents.columnVersion'), width: 10 },
  { key: 'last_seen', header: t('agents.columnLastSeen'), width: 20 },
];

interface AgentsViewProps {
  agents: DashboardAgentInfo[];
}

export function AgentsView({ agents }: AgentsViewProps) {
  return (
    <Panel title={t('agents.title')}>
      <DataTable
        columns={AGENT_COLUMNS}
        data={agents}
        emptyMessage={t('dashboard.noAgentsRegistered')}
      />
    </Panel>
  );
}
