/**
 * Full-height activity log view
 */

import React from 'react';
import { ActivityLog } from '../../components/dashboard/ActivityLog.js';
import type { ActivityEntry } from '../dashboard-types.js';

interface LogsViewProps {
  entries: ActivityEntry[];
}

export function LogsView({ entries }: LogsViewProps) {
  return <ActivityLog entries={entries} height={24} />;
}
