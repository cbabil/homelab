/**
 * Server command handlers for the interactive CLI
 */

import type { CommandResult } from '../types.js';
import type { MCPClient } from '../../lib/mcp-client.js';
import type { ServerInfo } from '../../lib/server.js';
import { sanitizeForDisplay } from '../../lib/validation.js';
import { t } from '../../i18n/index.js';

export async function handleServerCommand(
  client: MCPClient,
  subcommand: string,
  _args: string[]
): Promise<CommandResult[]> {
  switch (subcommand) {
    case 'list': {
      try {
        const response = await client.callTool<{ servers: ServerInfo[] }>(
          'list_servers',
          {}
        );

        if (!response.success) {
          return [{ type: 'error', content: response.error || t('servers.failedToList') }];
        }

        const servers = response.data?.servers || [];

        if (servers.length === 0) {
          return [{ type: 'info', content: t('servers.noServersFound') }];
        }

        const results: CommandResult[] = [
          { type: 'info', content: t('servers.foundServers', { count: servers.length }) },
        ];

        for (const server of servers) {
          results.push({
            type: server.status === 'online' ? 'success' : 'info',
            content: t('servers.serverEntry', {
              id: server.id,
              name: server.name,
              hostname: server.hostname,
              status: server.status,
            }),
          });
        }

        return results;
      } catch (err) {
        return [
          {
            type: 'error',
            content: err instanceof Error ? err.message : t('servers.failedToList'),
          },
        ];
      }
    }

    default:
      return [
        {
          type: 'error',
          content: subcommand
            ? t('commands.server.unknownSubcommand', { subcommand: sanitizeForDisplay(subcommand) })
            : t('commands.server.usage'),
        },
      ];
  }
}
