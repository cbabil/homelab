/**
 * JWT Utility Functions
 *
 * Base64URL encoding/decoding, JWT parsing utilities, and security
 * validation helpers for JWT token manipulation.
 */

import type { JWT, JWTHeader, JWTPayload } from '@/types/jwt';

/**
 * Base64URL encode buffer to string
 */
export function base64URLEncode(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  const binary = Array.from(bytes, (byte) => String.fromCharCode(byte)).join('');
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

/**
 * Base64URL decode string to buffer
 */
export function base64URLDecode(input: string): ArrayBuffer {
  // Add padding if needed
  let padded = input;
  while (padded.length % 4) {
    padded += '=';
  }

  // Convert back to standard base64
  const base64 = padded.replace(/-/g, '+').replace(/_/g, '/');

  try {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer as ArrayBuffer;
  } catch (error) {
    throw new Error(`Invalid base64URL string: ${error}`);
  }
}

/**
 * Base64URL encode JSON object
 */
export function base64URLEncodeJSON(obj: unknown): string {
  const json = JSON.stringify(obj);
  const buffer = new TextEncoder().encode(json);
  return base64URLEncode(buffer.buffer);
}

/**
 * Base64URL decode to JSON object
 */
export function base64URLDecodeJSON<T = unknown>(input: string): T {
  const buffer = base64URLDecode(input);
  const json = new TextDecoder().decode(buffer);
  return JSON.parse(json) as T;
}

/**
 * Parse JWT token into components
 */
export function parseJWT(token: string): JWT | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      return null;
    }

    const [headerPart, payloadPart, signaturePart] = parts;

    const header = base64URLDecodeJSON<JWTHeader>(headerPart);
    const payload = base64URLDecodeJSON<JWTPayload>(payloadPart);

    // Validate header structure
    if (!isValidJWTHeader(header)) {
      return null;
    }

    return {
      header,
      payload,
      signature: signaturePart,
    };
  } catch (error) {
    console.error('Failed to parse JWT:', error);
    return null;
  }
}

/**
 * Get JWT token expiration timestamp
 */
export function getTokenExpiration(token: string): number | null {
  const jwt = parseJWT(token);
  return jwt?.payload.exp || null;
}

/**
 * Check if JWT token is expired
 */
export function isTokenExpired(token: string, clockToleranceSeconds = 30): boolean {
  const exp = getTokenExpiration(token);
  if (!exp) return true;

  const now = Math.floor(Date.now() / 1000);
  return exp <= now - clockToleranceSeconds;
}

/**
 * Get time until token expiration in milliseconds
 */
export function getTimeToExpiration(token: string): number {
  const exp = getTokenExpiration(token);
  if (!exp) return 0;

  const now = Date.now();
  const expMs = exp * 1000;
  return Math.max(0, expMs - now);
}

/**
 * Extract JWT ID (jti) from token
 */
export function getTokenId(token: string): string | null {
  const jwt = parseJWT(token);
  return jwt?.payload.jti || null;
}

/**
 * Extract user ID from JWT token
 */
export function getUserIdFromToken(token: string): string | null {
  const jwt = parseJWT(token);
  return jwt?.payload.sub || null;
}

/**
 * Validate JWT header structure
 */
function isValidJWTHeader(header: unknown): header is JWTHeader {
  if (!header || typeof header !== 'object') return false;

  const h = header as Record<string, unknown>;
  return h.alg === 'HS256' && h.typ === 'JWT' && (h.kid === undefined || typeof h.kid === 'string');
}

/**
 * Validate JWT payload structure
 */
export function isValidJWTPayload(payload: unknown): payload is JWTPayload {
  if (!payload || typeof payload !== 'object') return false;

  const p = payload as Record<string, unknown>;

  // Check required standard claims
  const hasRequiredClaims =
    typeof p.iss === 'string' &&
    typeof p.sub === 'string' &&
    typeof p.aud === 'string' &&
    typeof p.exp === 'number' &&
    typeof p.iat === 'number' &&
    typeof p.jti === 'string';

  // Check required custom claims
  const hasCustomClaims =
    typeof p.id === 'string' &&
    typeof p.username === 'string' &&
    typeof p.email === 'string' &&
    (p.role === 'admin' || p.role === 'user') &&
    typeof p.sessionId === 'string' &&
    typeof p.tokenType === 'string' &&
    Array.isArray(p.scope);

  return hasRequiredClaims && hasCustomClaims;
}

/**
 * Create JWT token string from parts
 */
export function createJWTString(header: JWTHeader, payload: JWTPayload, signature: string): string {
  const headerB64 = base64URLEncodeJSON(header);
  const payloadB64 = base64URLEncodeJSON(payload);
  return `${headerB64}.${payloadB64}.${signature}`;
}

/**
 * Generate a cryptographically secure random string using crypto.getRandomValues.
 * Returns a base-36 encoded string of the specified byte length.
 */
export function cryptoRandomString(byteLength = 16): string {
  const randomBytes = crypto.getRandomValues(new Uint8Array(byteLength));
  return Array.from(randomBytes, (b) => b.toString(36).padStart(2, '0')).join('');
}

/**
 * Generate secure random JWT ID
 */
export function generateJTI(): string {
  const timestamp = Date.now().toString(36);
  const random = cryptoRandomString(16);
  return `${timestamp}-${random}`;
}

/**
 * Validate token timing (exp, iat, nbf)
 */
export function validateTokenTiming(
  payload: JWTPayload,
  clockToleranceSeconds = 30
): { isValid: boolean; error?: string } {
  const now = Math.floor(Date.now() / 1000);
  const tolerance = clockToleranceSeconds;

  // Check expiration
  if (payload.exp <= now - tolerance) {
    return { isValid: false, error: 'Token expired' };
  }

  // Check issued at (not in future)
  if (payload.iat > now + tolerance) {
    return { isValid: false, error: 'Token issued in future' };
  }

  return { isValid: true };
}

/**
 * Sanitize token for logging (remove sensitive data)
 */
export function sanitizeTokenForLogging(token: string): Record<string, unknown> {
  const jwt = parseJWT(token);
  if (!jwt) return { error: 'Invalid token' };

  return {
    header: jwt.header,
    payload: {
      iss: jwt.payload.iss,
      sub: jwt.payload.sub,
      aud: jwt.payload.aud,
      exp: jwt.payload.exp,
      iat: jwt.payload.iat,
      jti: jwt.payload.jti,
      tokenType: jwt.payload.tokenType,
      role: jwt.payload.role,
      // Omit sensitive data like email, preferences, etc.
    },
  };
}

/**
 * Compare two JWT tokens for equality (ignoring signature)
 */
export function compareJWTPayloads(token1: string, token2: string): boolean {
  const jwt1 = parseJWT(token1);
  const jwt2 = parseJWT(token2);

  if (!jwt1 || !jwt2) return false;

  return JSON.stringify(jwt1.payload) === JSON.stringify(jwt2.payload);
}

/**
 * Extract token metadata for security logging
 */
export function extractTokenMetadata(token: string): Record<string, unknown> | null {
  const jwt = parseJWT(token);
  if (!jwt) return null;

  return {
    jti: jwt.payload.jti,
    sub: jwt.payload.sub,
    tokenType: jwt.payload.tokenType,
    role: jwt.payload.role,
    sessionId: jwt.payload.sessionId,
    exp: jwt.payload.exp,
    iat: jwt.payload.iat,
    scope: jwt.payload.scope,
  };
}
