/**
 * Types for the dashboard views and data layer
 */

export type ViewMode = 'dashboard' | 'agents' | 'logs' | 'settings';

export const VALID_VIEWS: ViewMode[] = ['dashboard', 'agents', 'logs', 'settings'];

export interface DashboardAgentInfo {
  id: string;
  server_id: string;
  status: string;
  version: string | null;
  last_seen: string | null;
}

export interface DashboardServerInfo {
  id: string;
  name: string;
  hostname: string;
  status: string;
}

export interface DashboardData {
  agents: DashboardAgentInfo[];
  servers: DashboardServerInfo[];
  loading: boolean;
  error: string | null;
  lastRefresh: Date | null;
}

export interface ActivityEntry {
  id: string;
  timestamp: Date;
  type: 'CMD' | 'OK' | 'ERR' | 'WARN' | 'SYS';
  message: string;
}

export const NAV_ITEMS = [
  { key: 'dashboard', label: 'dashboard' },
  { key: 'agents', label: 'agents' },
  { key: 'logs', label: 'logs' },
  { key: 'settings', label: 'settings' },
] as const;

let activityCounter = 0;

export function resetActivityCounter(): void {
  activityCounter = 0;
}

export function createActivityEntry(
  type: ActivityEntry['type'],
  message: string
): ActivityEntry {
  return {
    id: `act-${Date.now()}-${++activityCounter}`,
    timestamp: new Date(),
    type,
    message,
  };
}
