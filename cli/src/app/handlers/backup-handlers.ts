/**
 * Backup command handlers for the interactive CLI
 *
 * Returns signal strings that App.tsx processes to trigger
 * password prompt flows before executing the actual MCP calls.
 */

import path from 'path';
import type { CommandResult } from '../types.js';
import { SIGNALS } from '../signals.js';
import { sanitizeForDisplay } from '../../lib/validation.js';

const DEFAULT_BACKUP_PATH = './backup.enc';

function validatePath(inputPath: string): string | null {
  if (!inputPath) {
    return 'Path is required';
  }
  if (/[\0]/.test(inputPath)) {
    return 'Path contains invalid characters';
  }
  const normalized = path.normalize(inputPath);
  if (normalized.includes('..')) {
    return 'Path must not contain ".."';
  }
  return null;
}

export async function handleBackupCommand(
  subcommand: string,
  args: string[]
): Promise<CommandResult[]> {
  switch (subcommand) {
    case 'export': {
      const path = args[0] || DEFAULT_BACKUP_PATH;
      const pathError = validatePath(path);
      if (pathError) {
        return [{ type: 'error', content: pathError }];
      }
      return [{ type: 'system', content: `${SIGNALS.BACKUP_EXPORT}${path}` }];
    }

    case 'import': {
      if (!args[0]) {
        return [{ type: 'error', content: 'Usage: /backup import <path> [--overwrite]' }];
      }
      const path = args[0];
      const pathError = validatePath(path);
      if (pathError) {
        return [{ type: 'error', content: pathError }];
      }
      const overwrite = args.includes('--overwrite');
      const signal = overwrite
        ? `${SIGNALS.BACKUP_IMPORT_OVERWRITE}${path}`
        : `${SIGNALS.BACKUP_IMPORT}${path}`;
      return [{ type: 'system', content: signal }];
    }

    default:
      return [
        {
          type: 'error',
          content: subcommand
            ? `Unknown backup subcommand: ${sanitizeForDisplay(subcommand)}`
            : 'Usage: /backup <export|import> [args]',
        },
      ];
  }
}
