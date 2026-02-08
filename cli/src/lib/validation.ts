/**
 * Input validation for setup and registration flows.
 * Rules match the frontend validation in registrationValidation.ts.
 */

export interface ValidationResult {
  valid: boolean;
  error?: string;
}

export function validateUsername(value: string): ValidationResult {
  const trimmed = value.trim();

  if (!trimmed) {
    return { valid: false, error: 'Username is required' };
  }

  if (trimmed.length < 3) {
    return { valid: false, error: 'Username must be at least 3 characters' };
  }

  if (trimmed.length > 50) {
    return { valid: false, error: 'Username must be less than 50 characters' };
  }

  if (!/^[a-zA-Z0-9_-]+$/.test(trimmed)) {
    return {
      valid: false,
      error: 'Username can only contain letters, numbers, hyphens, and underscores',
    };
  }

  return { valid: true };
}

export function validatePassword(value: string): ValidationResult {
  if (!value) {
    return { valid: false, error: 'Password is required' };
  }

  if (value.length < 12) {
    return { valid: false, error: 'Password must be at least 12 characters' };
  }

  if (value.length > 128) {
    return { valid: false, error: 'Password must be less than 128 characters' };
  }

  if (!/[A-Z]/.test(value)) {
    return { valid: false, error: 'Password must contain an uppercase letter' };
  }

  if (!/[a-z]/.test(value)) {
    return { valid: false, error: 'Password must contain a lowercase letter' };
  }

  if (!/\d/.test(value)) {
    return { valid: false, error: 'Password must contain a number' };
  }

  if (!/[!@#$%^&*(),.?"':{}|<>]/.test(value)) {
    return { valid: false, error: 'Password must contain a special character' };
  }

  return { valid: true };
}

export function validateMcpUrl(url: string): ValidationResult {
  try {
    const parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return { valid: false, error: 'MCP URL must use http or https protocol' };
    }
    return { valid: true };
  } catch {
    return { valid: false, error: 'Invalid URL format' };
  }
}

/**
 * Strip ANSI escape codes and control characters from input
 * before echoing in error messages.
 * Covers CSI (\x1b[...), OSC (\x1b]... terminated by BEL or ST),
 * charset designations (\x1b(X), and Fe two-character sequences (\x1bM).
 */
export function sanitizeForDisplay(input: string): string {
  // eslint-disable-next-line no-control-regex
  return input.replace(/\x1b\[[0-9;]*[a-zA-Z]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[()*/+][^\x1b]?|\x1b[^[\]()*/+]/g, '')
    .replace(/[\x00-\x1f\x7f-\x9f]/g, '');
}
