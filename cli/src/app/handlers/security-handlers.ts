/**
 * Security command handlers for the interactive CLI
 */

import type { CommandResult, AppState } from '../types.js';
import { getLockedAccounts, unlockAccount } from '../../lib/security.js';
import { sanitizeForDisplay } from '../../lib/validation.js';
import { t } from '../../i18n/index.js';

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
        return [{ type: 'error', content: t('security.usageUnlock') }];
      }
      if (!state.username) {
        return [{ type: 'error', content: t('auth.mustBeLoggedIn') }];
      }
      const notes = args.slice(1).join(' ') || undefined;
      return executeUnlock(args[0], state.username, notes);
    }

    default:
      return [
        {
          type: 'error',
          content: subcommand
            ? t('commands.security.unknownSubcommand', { subcommand: sanitizeForDisplay(subcommand) })
            : t('commands.security.usage'),
        },
      ];
  }
}

async function executeListLocked(): Promise<CommandResult[]> {
  try {
    const accounts = await getLockedAccounts();

    if (accounts.length === 0) {
      return [{ type: 'info', content: t('security.noLockedAccounts') }];
    }

    const results: CommandResult[] = [
      { type: 'info', content: t('security.foundLockedAccounts', { count: accounts.length }) },
    ];

    for (const account of accounts) {
      results.push({
        type: 'error',
        content: t('security.lockedAccountEntry', {
          id: account.id,
          identifier: account.identifier,
          type: account.identifier_type,
          attempts: account.attempt_count,
          lockedAt: account.locked_at,
        }),
      });
    }

    return results;
  } catch (err) {
    return [
      {
        type: 'error',
        content: err instanceof Error ? err.message : t('security.failedToListLocked'),
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
      return [{ type: 'success', content: t('security.unlockSuccess', { lockId }) }];
    }

    return [{ type: 'error', content: result.error || t('security.failedToUnlock') }];
  } catch (err) {
    return [
      {
        type: 'error',
        content: err instanceof Error ? err.message : t('security.failedToUnlock'),
      },
    ];
  }
}
