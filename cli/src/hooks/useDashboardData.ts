/**
 * Hook for fetching and auto-refreshing dashboard data
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { listAgents } from '../lib/agent.js';
import { listServers } from '../lib/server.js';
import type { DashboardData } from '../app/dashboard-types.js';

interface UseDashboardDataOptions {
  refreshInterval?: number;
  enabled?: boolean;
}

interface UseDashboardDataResult extends DashboardData {
  refresh: () => Promise<void>;
}

export function useDashboardData({
  refreshInterval = 30000,
  enabled = true,
}: UseDashboardDataOptions = {}): UseDashboardDataResult {
  const [data, setData] = useState<DashboardData>({
    agents: [],
    servers: [],
    loading: true,
    error: null,
    lastRefresh: null,
  });

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(async () => {
    setData((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const [agents, servers] = await Promise.all([
        listAgents(),
        listServers(),
      ]);

      setData({
        agents: agents.map((a) => ({
          id: a.id,
          server_id: a.server_id,
          status: a.status,
          version: a.version,
          last_seen: a.last_seen,
        })),
        servers: servers.map((s) => ({
          id: s.id,
          name: s.name,
          hostname: s.hostname,
          status: s.status,
        })),
        loading: false,
        error: null,
        lastRefresh: new Date(),
      });
    } catch (err) {
      setData((prev) => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to fetch data',
      }));
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;

    refresh();

    intervalRef.current = setInterval(refresh, refreshInterval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [enabled, refreshInterval, refresh]);

  return { ...data, refresh };
}
