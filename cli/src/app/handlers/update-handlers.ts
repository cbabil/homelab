/**
 * Update command handlers for the interactive CLI
 */

import type { CommandResult } from '../types.js';
import type { MCPClient } from '../../lib/mcp-client.js';
import { t } from '../../i18n/index.js';

export async function handleUpdateCommand(
  client: MCPClient
): Promise<CommandResult[]> {
  const response = await client.callTool<{
    current_version: string;
    latest_version: string;
    update_available: boolean;
  }>('check_updates', {});

  if (!response.success) {
    return [{ type: 'error', content: response.error || t('updates.failedToCheck') }];
  }

  const data = response.data;
  if (!data) {
    return [{ type: 'error', content: t('updates.noInfoAvailable') }];
  }

  if (data.update_available) {
    return [
      { type: 'info', content: t('updates.currentVersion', { version: data.current_version }) },
      {
        type: 'success',
        content: t('updates.updateAvailable', { version: data.latest_version }),
      },
    ];
  }

  return [
    { type: 'success', content: t('updates.latestVersion', { version: data.current_version }) },
  ];
}
