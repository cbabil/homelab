/**
 * Input validation for setup and registration flows.
 * Rules match the frontend validation in registrationValidation.ts.
 */

import { t } from '../i18n/index.js';

export interface ValidationResult {
  valid: boolean;
  error?: string;
}

export function validateUsername(value: string): ValidationResult {
  const trimmed = value.trim();

  if (!trimmed) {
    return { valid: false, error: t('validation.usernameRequired') };
  }

  if (trimmed.length < 3) {
    return { valid: false, error: t('validation.usernameMinLength') };
  }

  if (trimmed.length > 50) {
    return { valid: false, error: t('validation.usernameMaxLength') };
  }

  if (!/^[a-zA-Z0-9_-]+$/.test(trimmed)) {
    return {
      valid: false,
      error: t('validation.usernameInvalidChars'),
    };
  }

  return { valid: true };
}

export function validatePassword(value: string): ValidationResult {
  if (!value) {
    return { valid: false, error: t('validation.passwordRequired') };
  }

  if (value.length < 12) {
    return { valid: false, error: t('validation.passwordMinLength') };
  }

  if (value.length > 128) {
    return { valid: false, error: t('validation.passwordMaxLength') };
  }

  if (!/[A-Z]/.test(value)) {
    return { valid: false, error: t('validation.passwordUppercase') };
  }

  if (!/[a-z]/.test(value)) {
    return { valid: false, error: t('validation.passwordLowercase') };
  }

  if (!/\d/.test(value)) {
    return { valid: false, error: t('validation.passwordNumber') };
  }

  if (!/[!@#$%^&*(),.?"':{}|<>]/.test(value)) {
    return { valid: false, error: t('validation.passwordSpecialChar') };
  }

  return { valid: true };
}

export function validateMcpUrl(url: string): ValidationResult {
  try {
    const parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return { valid: false, error: t('validation.mcpUrlProtocol') };
    }
    return { valid: true };
  } catch {
    return { valid: false, error: t('validation.invalidUrlFormat') };
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
