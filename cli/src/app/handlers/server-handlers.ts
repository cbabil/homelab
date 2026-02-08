/**
 * Server command handlers for the interactive CLI
 */

import type { CommandResult } from '../types.js';
import type { MCPClient } from '../../lib/mcp-client.js';
import type { ServerInfo } from '../../lib/server.js';
import { sanitizeForDisplay } from '../../lib/validation.js';

export type { ServerInfo };

export async function handleServerCommand(
  client: MCPClient,
  subcommand: string,
  _args: string[]
): Promise<CommandResult[]> {
  switch (subcommand) {
    case 'list': {
      const response = await client.callTool<{ servers: ServerInfo[] }>(
        'list_servers',
        {}
      );

      if (!response.success) {
        return [{ type: 'error', content: response.error || 'Failed to list servers' }];
      }

      const servers = response.data?.servers || [];

      if (servers.length === 0) {
        return [{ type: 'info', content: 'No servers found.' }];
      }

      const results: CommandResult[] = [
        { type: 'info', content: `Found ${servers.length} server(s):` },
      ];

      for (const server of servers) {
        results.push({
          type: server.status === 'online' ? 'success' : 'info',
          content: `  [${server.id}] ${server.name} - ${server.hostname}`,
        });
      }

      return results;
    }

    default:
      return [
        {
          type: 'error',
          content: subcommand
            ? `Unknown server subcommand: ${sanitizeForDisplay(subcommand)}`
            : 'Usage: server <list>',
        },
      ];
  }
}
