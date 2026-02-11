/**
 * Security management module
 *
 * Handles account lockout management via MCP server.
 */

import { getMCPClient, MCPResponse } from './mcp-client.js';
import { t } from '../i18n/index.js';

export interface LockedAccount {
  id: string;
  identifier: string;
  identifier_type: string;
  attempt_count: number;
  locked_at: string;
  lock_expires_at: string | null;
  ip_address: string;
  unlocked_at?: string;
  unlocked_by?: string;
  notes?: string;
}

export interface LockedAccountsResponse {
  accounts: LockedAccount[];
  count: number;
}

export interface UnlockResult {
  success: boolean;
  error?: string;
  lock_id?: string;
}

/**
 * Get all locked accounts via MCP
 */
export async function getLockedAccounts(
  includeExpired: boolean = false,
  includeUnlocked: boolean = false
): Promise<LockedAccount[]> {
  const client = getMCPClient();
  const response = await client.callTool<LockedAccountsResponse>(
    'get_locked_accounts',
    {
      include_expired: includeExpired,
      include_unlocked: includeUnlocked,
    }
  );

  if (response.success && response.data?.accounts) {
    return response.data.accounts;
  }

  return [];
}

/**
 * Unlock a specific account via MCP
 */
export async function unlockAccount(
  lockId: string,
  adminUsername: string,
  notes?: string
): Promise<UnlockResult> {
  const client = getMCPClient();
  const response = await client.callTool<{ lock_id: string }>(
    'update_account_lock',
    {
      lock_id: lockId,
      action: 'unlock',
      admin_username: adminUsername,
      notes: notes || t('security.unlockedViaCli', { username: adminUsername }),
    }
  );

  if (response.success) {
    return {
      success: true,
      lock_id: lockId,
    };
  }

  return {
    success: false,
    error: response.error || response.message || t('errors.failedToUnlockAccount'),
  };
}
