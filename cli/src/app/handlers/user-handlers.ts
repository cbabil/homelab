/**
 * User command handlers for the interactive CLI
 *
 * Returns signal strings that App.tsx processes to trigger
 * password prompt flows before executing the actual MCP calls.
 */

import type { CommandResult } from '../types.js';
import { SIGNALS } from '../signals.js';
import { sanitizeForDisplay } from '../../lib/validation.js';
import { t } from '../../i18n/index.js';

export async function handleUserCommand(
  subcommand: string,
  args: string[]
): Promise<CommandResult[]> {
  switch (subcommand) {
    case 'reset-password': {
      const username = args[0]?.trim();
      if (!username) {
        return [{ type: 'error', content: t('users.usageResetPassword') }];
      }
      if (username.length < 3 || username.length > 50 || !/^[a-zA-Z0-9_-]+$/.test(username)) {
        return [{ type: 'error', content: t('users.usernameValidation') }];
      }
      return [{ type: 'system', content: `${SIGNALS.RESET_PASSWORD}${username}` }];
    }

    default:
      return [
        {
          type: 'error',
          content: subcommand
            ? t('commands.user.unknownSubcommand', { subcommand: sanitizeForDisplay(subcommand) })
            : t('commands.user.usage'),
        },
      ];
  }
}
