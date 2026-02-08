/**
 * Server management module
 *
 * Wraps MCP server list operations.
 */

import { getMCPClient } from './mcp-client.js';

export interface ServerInfo {
  id: string;
  name: string;
  hostname: string;
  status: string;
}

interface ServerListResponse {
  servers: ServerInfo[];
}

/**
 * List all servers via MCP
 */
export async function listServers(): Promise<ServerInfo[]> {
  const client = getMCPClient();
  const response = await client.callTool<ServerListResponse>(
    'list_servers',
    {}
  );

  if (!response.success) {
    throw new Error(response.error || 'Failed to list servers');
  }

  return response.data?.servers ?? [];
}
