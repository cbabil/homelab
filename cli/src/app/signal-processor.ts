/**
 * Signal processor — classifies CommandResult signals into typed actions.
 *
 * Separates signal parsing (pure logic) from side effects (App.tsx).
 */

import { SIGNALS, parseSignal } from './signals.js';
import type { CommandResult } from './types.js';
import { VALID_VIEWS } from './dashboard-types.js';
import type { ViewMode } from './dashboard-types.js';

export type SignalAction =
  | { kind: 'clear' }
  | { kind: 'logout' }
  | { kind: 'login' }
  | { kind: 'refresh' }
  | { kind: 'setup' }
  | { kind: 'reset_password'; username: string }
  | { kind: 'backup_export'; path: string }
  | { kind: 'backup_import'; path: string; overwrite: boolean }
  | { kind: 'view'; target: ViewMode }
  | { kind: 'message'; result: CommandResult };

export function classifySignal(result: CommandResult): SignalAction {
  if (result.content === SIGNALS.CLEAR) return { kind: 'clear' };
  if (result.content === SIGNALS.LOGOUT) return { kind: 'logout' };
  if (result.content === SIGNALS.LOGIN) return { kind: 'login' };
  if (result.content === SIGNALS.REFRESH) return { kind: 'refresh' };
  if (result.content === SIGNALS.SETUP) return { kind: 'setup' };

  const resetUsername = parseSignal(result.content, SIGNALS.RESET_PASSWORD);
  if (resetUsername !== null) {
    return { kind: 'reset_password', username: resetUsername };
  }

  const exportPath = parseSignal(result.content, SIGNALS.BACKUP_EXPORT);
  if (exportPath !== null) {
    return { kind: 'backup_export', path: exportPath };
  }

  // IMPORTANT: Check BACKUP_IMPORT_OVERWRITE before BACKUP_IMPORT
  // because parseSignal uses startsWith(), and __BACKUP_IMPORT__ is
  // a string prefix of __BACKUP_IMPORT_OVERWRITE__.
  const overwritePath = parseSignal(result.content, SIGNALS.BACKUP_IMPORT_OVERWRITE);
  if (overwritePath !== null) {
    return { kind: 'backup_import', path: overwritePath, overwrite: true };
  }

  const importPath = parseSignal(result.content, SIGNALS.BACKUP_IMPORT);
  if (importPath !== null) {
    return { kind: 'backup_import', path: importPath, overwrite: false };
  }

  const viewTarget = parseSignal(result.content, SIGNALS.VIEW);
  if (viewTarget !== null && VALID_VIEWS.includes(viewTarget as ViewMode)) {
    return { kind: 'view', target: viewTarget as ViewMode };
  }

  return { kind: 'message', result };
}
