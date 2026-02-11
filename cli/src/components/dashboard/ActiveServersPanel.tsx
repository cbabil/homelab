/**
 * Active servers panel with a DataTable showing server info
 */

import React from 'react';
import { Panel } from './Panel.js';
import { DataTable, type DataColumn } from './DataTable.js';
import { StatusBadge } from './StatusBadge.js';
import type { BadgeStatus } from '../../app/theme.js';
import { t } from '../../i18n/index.js';

export interface ServerRow {
  id: string;
  name: string;
  hostname: string;
  status: string;
}

function mapServerStatus(status: string): BadgeStatus {
  switch (status) {
    case 'online':
      return 'active';
    case 'offline':
      return 'offline';
    case 'maintenance':
      return 'locked';
    default:
      return 'idle';
  }
}

const SERVER_COLUMNS: DataColumn<ServerRow>[] = [
  { key: 'id', header: t('servers.columnId'), width: 10 },
  { key: 'name', header: t('servers.columnName'), width: 14 },
  { key: 'hostname', header: t('servers.columnHostname'), width: 16 },
  {
    key: 'status',
    header: t('servers.columnStatus'),
    width: 12,
    render: (row: ServerRow) => (
      <StatusBadge status={mapServerStatus(row.status)} />
    ),
  },
];

interface ActiveServersPanelProps {
  servers: ServerRow[];
}

export function ActiveServersPanel({ servers }: ActiveServersPanelProps) {
  return (
    <Panel title={t('dashboard.activeServers')}>
      <DataTable
        columns={SERVER_COLUMNS}
        data={servers}
        emptyMessage={t('dashboard.noServersRegistered')}
      />
    </Panel>
  );
}
