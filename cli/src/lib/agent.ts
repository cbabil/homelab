/**
 * Agent management module
 *
 * Handles agent lifecycle operations via MCP server.
 */

import { getMCPClient, MCPResponse } from './mcp-client.js';

export interface AgentInfo {
  id: string;
  server_id: string;
  status: string;
  version: string | null;
  last_seen: string | null;
  registered_at: string | null;
  is_connected?: boolean;
}

export interface AgentListResponse {
  agents: AgentInfo[];
  count: number;
}

export interface AgentResult {
  success: boolean;
  data?: Record<string, unknown>;
  error?: string;
  message?: string;
}

export interface AgentHealthData {
  agent_id: string;
  server_id: string;
  status: string;
  health: string;
  is_connected: boolean;
  is_stale: boolean;
  version: string | null;
  last_seen: string | null;
  registered_at: string | null;
}

export interface AgentVersionData {
  current_version: string;
  latest_version: string;
  update_available: boolean;
}

export interface AgentPingData {
  agent_id: string;
  responsive: boolean;
  latency_ms: number | null;
}

export interface StaleAgentInfo {
  agent_id: string;
  server_id: string;
  last_heartbeat: string;
}

export interface StaleAgentsResponse {
  stale_count: number;
  agents: StaleAgentInfo[];
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
    error: response.error || response.message || 'Failed to install agent',
  };
}

/**
 * Uninstall an agent from a server via MCP
 */
export async function uninstallAgent(serverId: string): Promise<AgentResult> {
  const client = getMCPClient();
  const response = await client.callTool<{ agent_id: string }>(
    'uninstall_agent',
    { server_id: serverId }
  );

  if (response.success) {
    return {
      success: true,
      data: response.data,
      message: response.message,
    };
  }

  return {
    success: false,
    error: response.error || response.message || 'Failed to uninstall agent',
  };
}

/**
 * Get agent status for a server via MCP
 */
export async function getAgentStatus(serverId: string): Promise<AgentInfo | null> {
  const client = getMCPClient();
  const response = await client.callTool<AgentInfo>(
    'get_agent_status',
    { server_id: serverId }
  );

  if (response.success && response.data) {
    return response.data;
  }

  return null;
}

/**
 * Revoke an agent token via MCP
 */
export async function revokeAgent(serverId: string): Promise<AgentResult> {
  const client = getMCPClient();
  const response = await client.callTool<{ agent_id: string }>(
    'revoke_agent_token',
    { server_id: serverId }
  );

  if (response.success) {
    return {
      success: true,
      data: response.data,
      message: response.message,
    };
  }

  return {
    success: false,
    error: response.error || response.message || 'Failed to revoke agent',
  };
}

/**
 * Ping an agent via MCP
 */
export async function pingAgent(
  serverId: string,
  timeout: number = 5
): Promise<AgentPingData | null> {
  const client = getMCPClient();
  const response = await client.callTool<AgentPingData>(
    'ping_agent',
    { server_id: serverId, timeout }
  );

  if (response.success && response.data) {
    return response.data;
  }

  return null;
}

/**
 * Check agent health via MCP
 */
export async function checkAgentHealth(serverId: string): Promise<AgentHealthData | null> {
  const client = getMCPClient();
  const response = await client.callTool<AgentHealthData>(
    'check_agent_health',
    { server_id: serverId }
  );

  if (response.success && response.data) {
    return response.data;
  }

  return null;
}

/**
 * Check agent version via MCP
 */
export async function checkAgentVersion(serverId: string): Promise<AgentVersionData | null> {
  const client = getMCPClient();
  const response = await client.callTool<AgentVersionData>(
    'check_agent_version',
    { server_id: serverId }
  );

  if (response.success && response.data) {
    return response.data;
  }

  return null;
}

/**
 * Trigger agent update via MCP
 */
export async function triggerAgentUpdate(serverId: string): Promise<AgentResult> {
  const client = getMCPClient();
  const response = await client.callTool<{ agent_id: string; status: string }>(
    'trigger_agent_update',
    { server_id: serverId }
  );

  if (response.success) {
    return {
      success: true,
      data: response.data,
      message: response.message,
    };
  }

  return {
    success: false,
    error: response.error || response.message || 'Failed to trigger update',
  };
}

/**
 * List stale agents via MCP
 */
export async function listStaleAgents(): Promise<StaleAgentsResponse | null> {
  const client = getMCPClient();
  const response = await client.callTool<StaleAgentsResponse>(
    'list_stale_agents',
    {}
  );

  if (response.success && response.data) {
    return response.data;
  }

  return null;
}

/**
 * Reset agent status via MCP
 */
export async function resetAgentStatus(
  serverId?: string
): Promise<AgentResult> {
  const client = getMCPClient();
  const params = serverId ? { server_id: serverId } : {};
  const response = await client.callTool<{ reset_count?: number; agent_id?: string }>(
    'reset_agent_status',
    params
  );

  if (response.success) {
    return {
      success: true,
      data: response.data,
      message: response.message,
    };
  }

  return {
    success: false,
    error: response.error || response.message || 'Failed to reset agent status',
  };
}

export interface RotateTokenData {
  agent_id: string;
  server_id: string;
  grace_period_seconds: number;
  token_expires_at: string;
}

/**
 * Rotate agent token via MCP
 */
export async function rotateAgentToken(serverId: string): Promise<AgentResult> {
  const client = getMCPClient();
  const response = await client.callTool<RotateTokenData>(
    'rotate_agent_token',
    { server_id: serverId }
  );

  if (response.success && response.data) {
    return {
      success: true,
      data: response.data as unknown as Record<string, unknown>,
      message: response.message,
    };
  }

  return {
    success: false,
    error: response.error || response.message || 'Failed to rotate agent token',
  };
}
