/**
 * Update command handlers for the interactive CLI
 */

import type { CommandResult } from '../types.js';
import type { MCPClient } from '../../lib/mcp-client.js';

export async function handleUpdateCommand(
  client: MCPClient
): Promise<CommandResult[]> {
  const response = await client.callTool<{
    current_version: string;
    latest_version: string;
    update_available: boolean;
  }>('check_updates', {});

  if (!response.success) {
    return [{ type: 'error', content: response.error || 'Failed to check updates' }];
  }

  const data = response.data;
  if (!data) {
    return [{ type: 'error', content: 'No update information available' }];
  }

  if (data.update_available) {
    return [
      { type: 'info', content: `Current version: ${data.current_version}` },
      {
        type: 'success',
        content: `Update available: ${data.latest_version}`,
      },
    ];
  }

  return [
    { type: 'success', content: `You are running the latest version: ${data.current_version}` },
  ];
}
