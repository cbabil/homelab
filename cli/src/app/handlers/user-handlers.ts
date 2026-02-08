/**
 * User command handlers for the interactive CLI
 *
 * Returns signal strings that App.tsx processes to trigger
 * password prompt flows before executing the actual MCP calls.
 */

import type { CommandResult } from '../types.js';
import { SIGNALS } from '../signals.js';
import { sanitizeForDisplay } from '../../lib/validation.js';

export async function handleUserCommand(
  subcommand: string,
  args: string[]
): Promise<CommandResult[]> {
  switch (subcommand) {
    case 'reset-password': {
      const username = args[0]?.trim();
      if (!username) {
        return [{ type: 'error', content: 'Usage: /user reset-password <username>' }];
      }
      if (username.length < 3 || username.length > 50 || !/^[a-zA-Z0-9_-]+$/.test(username)) {
        return [{ type: 'error', content: 'Username must be 3-50 characters (letters, numbers, _ or -)' }];
      }
      return [{ type: 'system', content: `${SIGNALS.RESET_PASSWORD}${username}` }];
    }

    default:
      return [
        {
          type: 'error',
          content: subcommand
            ? `Unknown user subcommand: ${sanitizeForDisplay(subcommand)}`
            : 'Usage: /user <reset-password> <username>',
        },
      ];
  }
}
