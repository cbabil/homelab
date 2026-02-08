/**
 * Dashboard theme constants - hacker terminal green monochrome
 */

export const COLORS = {
  primary: 'green',
  bright: 'greenBright',
  dim: 'gray',
  error: 'red',
  warn: 'yellow',
} as const;

export const BORDER = {
  style: 'single' as const,
  color: 'green',
};

export type BadgeStatus = 'active' | 'idle' | 'offline' | 'locked';

export const BADGES: Record<BadgeStatus, { label: string; color: string }> = {
  active: { label: 'ACTIVE', color: COLORS.bright },
  idle: { label: 'IDLE', color: COLORS.primary },
  offline: { label: 'OFFLINE', color: COLORS.dim },
  locked: { label: 'LOCKED', color: COLORS.error },
};

export function formatPanelHeader(text: string): string {
  return `[ ${text.toUpperCase()} ]`;
}

export function formatPrompt(user: string, host: string): string {
  return `${user}@${host}:~$ `;
}

export function formatTimestamp(date: Date): string {
  const h = String(date.getHours()).padStart(2, '0');
  const m = String(date.getMinutes()).padStart(2, '0');
  const s = String(date.getSeconds()).padStart(2, '0');
  return `${h}:${m}:${s}`;
}

export const PROGRESS_CHARS = {
  filled: '#',
  empty: '-',
} as const;
