/**
 * Agent management module
 *
 * Handles agent lifecycle operations via MCP server.
 */

import { getMCPClient } from './mcp-client.js';
import { t } from '../i18n/index.js';

export interface AgentInfo {
  id: string;
  server_id: string;
  status: string;
  version: string | null;
  last_seen: string | null;
  registered_at: string | null;
  is_connected?: boolean;
}

export interface RotateTokenData {
  agent_id: string;
  server_id: string;
  grace_period_seconds: number;
  token_expires_at: string;
}

interface AgentListResponse {
  agents: AgentInfo[];
  count: number;
}

interface AgentResult {
  success: boolean;
  data?: Record<string, unknown>;
  error?: string;
  message?: string;
}

/**
 * List all agents via MCP
 */
export async function listAgents(): Promise<AgentInfo[]> {
  const client = getMCPClient();
  const response = await client.callTool<AgentListResponse>('list_agents', {});

  if (response.success && response.data?.agents) {
    return response.data.agents;
  }

  return [];
}

/**
 * Install an agent on a server via MCP
 */
export async function installAgent(serverId: string): Promise<AgentResult> {
  const client = getMCPClient();
  const response = await client.callTool<{ agent_id: string; version: string }>(
    'install_agent',
    { server_id: serverId }
  );

  if (response.success && response.data) {
    return {
      success: true,
      data: response.data,
      message: response.message,
    };
  }

  return {
    success: false,
    error: response.error || response.message || t('errors.failedToInstallAgent'),
  };
}
