/**
 * Centralized signal constants for command-to-App communication.
 *
 * Handlers return signal strings via CommandResult.content.
 * App.tsx intercepts them to trigger UI flows (prompts, view switches, etc.).
 */

export const SIGNALS = {
  CLEAR: '__CLEAR__',
  LOGOUT: '__LOGOUT__',
  LOGIN: '__LOGIN__',
  REFRESH: '__REFRESH__',
  SETUP: '__SETUP__',
  RESET_PASSWORD: '__RESET_PASSWORD__',
  BACKUP_EXPORT: '__BACKUP_EXPORT__',
  // IMPORTANT: BACKUP_IMPORT_OVERWRITE must be checked before BACKUP_IMPORT
  // in signal-processor.ts since BACKUP_IMPORT is a prefix of BACKUP_IMPORT_OVERWRITE.
  BACKUP_IMPORT: '__BACKUP_IMPORT__',
  BACKUP_IMPORT_OVERWRITE: '__BACKUP_IMPORT_OVERWRITE__',
  VIEW: '__VIEW__',
} as const;

/**
 * Parse a signal string that carries a payload (e.g. "__VIEW__agents").
 * Returns the payload or null if the signal does not match.
 */
export function parseSignal(
  content: string,
  signal: string
): string | null {
  if (content.startsWith(signal)) {
    return content.slice(signal.length);
  }
  return null;
}

