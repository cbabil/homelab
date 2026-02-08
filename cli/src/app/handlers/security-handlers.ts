/**
 * Security command handlers for the interactive CLI
 */

import type { CommandResult, AppState } from '../types.js';
import { getLockedAccounts, unlockAccount } from '../../lib/security.js';
import { sanitizeForDisplay } from '../../lib/validation.js';

export async function handleSecurityCommand(
  subcommand: string,
  args: string[],
  state: AppState
): Promise<CommandResult[]> {
  switch (subcommand) {
    case 'list-locked':
      return executeListLocked();

    case 'unlock': {
      if (!args[0]) {
        return [{ type: 'error', content: 'Usage: /security unlock <lock-id> [notes]' }];
      }
      if (!state.username) {
        return [{ type: 'error', content: 'You must be logged in to unlock accounts' }];
      }
      const notes = args.slice(1).join(' ') || undefined;
      return executeUnlock(args[0], state.username, notes);
    }

    default:
      return [
        {
          type: 'error',
          content: subcommand
            ? `Unknown security subcommand: ${sanitizeForDisplay(subcommand)}`
            : 'Usage: /security <list-locked|unlock> [args]',
        },
      ];
  }
}

async function executeListLocked(): Promise<CommandResult[]> {
  try {
    const accounts = await getLockedAccounts();

    if (accounts.length === 0) {
      return [{ type: 'info', content: 'No locked accounts found.' }];
    }

    const results: CommandResult[] = [
      { type: 'info', content: `Found ${accounts.length} locked account(s):` },
    ];

    for (const account of accounts) {
      results.push({
        type: 'error',
        content: `  [${account.id}] ${account.identifier} (${account.identifier_type}) - ${account.attempt_count} attempts - locked ${account.locked_at}`,
      });
    }

    return results;
  } catch (err) {
    return [
      {
        type: 'error',
        content: err instanceof Error ? err.message : 'Failed to list locked accounts',
      },
    ];
  }
}

async function executeUnlock(
  lockId: string,
  adminUsername: string,
  notes?: string
): Promise<CommandResult[]> {
  try {
    const result = await unlockAccount(lockId, adminUsername, notes);

    if (result.success) {
      return [{ type: 'success', content: `Account lock ${lockId} unlocked successfully` }];
    }

    return [{ type: 'error', content: result.error || 'Failed to unlock account' }];
  } catch (err) {
    return [
      {
        type: 'error',
        content: err instanceof Error ? err.message : 'Failed to unlock account',
      },
    ];
  }
}
