import { useState, useEffect, useCallback } from 'react';
import {
  initMCPClient,
  closeMCPClient,
  getMCPClient,
} from '../lib/mcp-client.js';

interface UseMCPResult {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  callTool: <T = unknown>(
    tool: string,
    args?: Record<string, unknown>
  ) => Promise<{ success: boolean; data?: T; error?: string }>;
}

export function useMCP(mcpUrl?: string): UseMCPResult {
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const url =
      mcpUrl || process.env.MCP_SERVER_URL || 'http://localhost:8000/mcp';

    setConnecting(true);
    initMCPClient(url)
      .then(() => {
        setConnected(true);
        setConnecting(false);
      })
      .catch((err: Error) => {
        setError(err.message);
        setConnecting(false);
      });

    return () => {
      closeMCPClient();
    };
  }, [mcpUrl]);

  const callTool = useCallback(
    async <T = unknown>(tool: string, args?: Record<string, unknown>) => {
      const client = getMCPClient();
      return client.callTool(tool, args) as Promise<{
        success: boolean;
        data?: T;
        error?: string;
      }>;
    },
    []
  );

  return { connected, connecting, error, callTool };
}
