/**
 * JWT Service Core Implementation
 *
 * Complete JWT token system using Web Crypto API for HS256 signing.
 * Includes token generation, verification, refresh, and revocation.
 */

import type {
  JWTService,
  JWTGenerationOptions,
  JWTValidationResult,
  TokenPair,
  JWTConfig,
  BlacklistEntry,
  TokenBlacklist,
  JWTHeader,
  JWTPayload,
  JWT,
} from '@/types/jwt';
import { DEFAULT_JWT_CONFIG } from '@/types/jwt';

import { keyManager } from './keyManager';
import {
  base64URLEncode,
  base64URLEncodeJSON,
  parseJWT,
  generateJTI,
  validateTokenTiming,
  isValidJWTPayload,
} from '@/utils/jwtUtils';

/**
 * In-memory token blacklist implementation
 */
class MemoryTokenBlacklist implements TokenBlacklist {
  private blacklist = new Map<string, BlacklistEntry>();

  async add(entry: BlacklistEntry): Promise<void> {
    this.blacklist.set(entry.jti, entry);
  }

  async isBlacklisted(jti: string): Promise<boolean> {
    return this.blacklist.has(jti);
  }

  async cleanup(): Promise<void> {
    const now = Math.floor(Date.now() / 1000);
    for (const [jti, entry] of this.blacklist.entries()) {
      if (entry.exp <= now) {
        this.blacklist.delete(jti);
      }
    }
  }
}

class JWTServiceImpl implements JWTService {
  private config: JWTConfig = DEFAULT_JWT_CONFIG;
  private blacklist: TokenBlacklist = new MemoryTokenBlacklist();
  private isInitialized = false;
  private cleanupIntervalId: ReturnType<typeof setInterval> | null = null;

  /**
   * Initialize JWT service
   */
  async initialize(config?: Partial<JWTConfig>): Promise<void> {
    if (config) {
      this.config = { ...DEFAULT_JWT_CONFIG, ...config };
    }

    await keyManager.initialize();
    this.isInitialized = true;

    // Clear any existing interval before creating a new one
    if (this.cleanupIntervalId) {
      clearInterval(this.cleanupIntervalId);
    }

    // Start periodic blacklist cleanup
    this.cleanupIntervalId = setInterval(() => {
      this.blacklist.cleanup().catch(console.error);
    }, 300000); // 5 minutes
  }

  /**
   * Generate JWT token
   */
  async generateToken(options: JWTGenerationOptions): Promise<string> {
    this.ensureInitialized();

    const activeKey = await keyManager.getActiveKey();
    if (!activeKey) {
      throw new Error('No active signing key available');
    }

    const now = Math.floor(Date.now() / 1000);
    const ttl =
      options.tokenType === 'access' ? this.config.accessTokenTTL : this.config.refreshTokenTTL;

    // Build JWT header
    const header: JWTHeader = {
      alg: 'HS256',
      typ: 'JWT',
      kid: activeKey.keyId,
    };

    // Build JWT payload
    const payload: JWTPayload = {
      // Standard claims
      iss: this.config.issuer,
      sub: options.userId,
      aud: this.config.audience,
      exp: now + ttl,
      iat: now,
      jti: generateJTI(),

      // User claims
      id: options.userId,
      username: options.username,
      email: options.email,
      role: options.role,
      preferences: options.preferences,

      // Session claims
      sessionId: options.sessionId,
      ipAddress: options.ipAddress,
      userAgent: options.userAgent,
      startTime: now,
      lastActivity: now,

      // Security claims
      tokenType: options.tokenType,
      scope: options.scope || ['read'],
      authMethod: 'password',
      riskLevel: 'low',
    };

    // Create signature
    const signature = await this.signToken(header, payload, activeKey.key);

    // Build final token
    const headerB64 = base64URLEncodeJSON(header);
    const payloadB64 = base64URLEncodeJSON(payload);
    const token = `${headerB64}.${payloadB64}.${signature}`;

    // Log token generation
    this.logSecurityEvent('token_generated', {
      tokenId: payload.jti,
      userId: options.userId,
      tokenType: options.tokenType,
      expiresIn: ttl,
    });

    return token;
  }

  /**
   * Validate JWT token
   */
  async validateToken(token: string): Promise<JWTValidationResult> {
    this.ensureInitialized();

    try {
      // Parse token
      const jwt = parseJWT(token);
      if (!jwt) {
        return {
          isValid: false,
          error: { code: 'MALFORMED', message: 'Invalid token format' },
        };
      }

      // Validate payload structure
      if (!isValidJWTPayload(jwt.payload)) {
        return {
          isValid: false,
          error: { code: 'MALFORMED', message: 'Invalid payload structure' },
        };
      }

      // Check algorithm
      if (jwt.header.alg !== 'HS256') {
        return {
          isValid: false,
          error: { code: 'ALGORITHM_MISMATCH', message: 'Unsupported algorithm' },
        };
      }

      // Check timing
      const timingValidation = validateTokenTiming(jwt.payload, this.config.clockTolerance);
      if (!timingValidation.isValid) {
        return {
          isValid: false,
          error: {
            code: 'EXPIRED',
            message: timingValidation.error || 'Token timing invalid',
          },
        };
      }

      // Check audience and issuer
      if (jwt.payload.aud !== this.config.audience) {
        return {
          isValid: false,
          error: { code: 'AUDIENCE_MISMATCH', message: 'Invalid audience' },
        };
      }

      if (jwt.payload.iss !== this.config.issuer) {
        return {
          isValid: false,
          error: { code: 'ISSUER_MISMATCH', message: 'Invalid issuer' },
        };
      }

      // Check blacklist
      if (await this.blacklist.isBlacklisted(jwt.payload.jti)) {
        return {
          isValid: false,
          error: { code: 'REVOKED', message: 'Token has been revoked' },
        };
      }

      // Verify signature
      const isSignatureValid = await this.verifySignature(jwt, token);
      if (!isSignatureValid) {
        return {
          isValid: false,
          error: { code: 'INVALID_SIGNATURE', message: 'Invalid token signature' },
        };
      }

      // Log successful validation
      this.logSecurityEvent('token_validated', {
        tokenId: jwt.payload.jti,
        userId: jwt.payload.sub,
        tokenType: jwt.payload.tokenType,
      });

      return { isValid: true, payload: jwt.payload };
    } catch (error) {
      this.logSecurityEvent('token_validation_error', {
        error: String(error),
        token: token.substring(0, 50) + '...',
      });

      return {
        isValid: false,
        error: {
          code: 'MALFORMED',
          message: `Validation failed: ${error}`,
        },
      };
    }
  }

  /**
   * Refresh token pair
   */
  async refreshToken(refreshToken: string): Promise<TokenPair> {
    this.ensureInitialized();

    // Validate refresh token
    const validation = await this.validateToken(refreshToken);
    if (!validation.isValid || !validation.payload) {
      throw new Error(`Invalid refresh token: ${validation.error?.message}`);
    }

    const payload = validation.payload;
    if (payload.tokenType !== 'refresh') {
      throw new Error('Token is not a refresh token');
    }

    // Generate new token pair
    const options: JWTGenerationOptions = {
      userId: payload.id,
      username: payload.username,
      email: payload.email,
      role: payload.role,
      sessionId: payload.sessionId,
      ipAddress: payload.ipAddress,
      userAgent: payload.userAgent,
      tokenType: 'access',
      scope: payload.scope,
      preferences: payload.preferences,
    };

    const [newAccessToken, newRefreshToken] = await Promise.all([
      this.generateToken({ ...options, tokenType: 'access' }),
      this.generateToken({ ...options, tokenType: 'refresh' }),
    ]);

    // Revoke old refresh token
    await this.revokeToken(refreshToken, 'revoke');

    this.logSecurityEvent('token_refreshed', {
      userId: payload.id,
      oldTokenId: payload.jti,
      sessionId: payload.sessionId,
    });

    return {
      accessToken: newAccessToken,
      refreshToken: newRefreshToken,
      expiresIn: this.config.accessTokenTTL,
      refreshExpiresIn: this.config.refreshTokenTTL,
    };
  }

  /**
   * Revoke token
   */
  async revokeToken(token: string, reason: BlacklistEntry['reason']): Promise<void> {
    this.ensureInitialized();

    const jwt = parseJWT(token);
    if (!jwt) {
      throw new Error('Invalid token format');
    }

    const entry: BlacklistEntry = {
      jti: jwt.payload.jti,
      exp: jwt.payload.exp,
      reason,
      timestamp: Math.floor(Date.now() / 1000),
    };

    await this.blacklist.add(entry);

    this.logSecurityEvent('token_revoked', {
      tokenId: jwt.payload.jti,
      userId: jwt.payload.sub,
      reason,
    });
  }

  /**
   * Decode token without validation
   */
  decodeToken(token: string): JWT | null {
    return parseJWT(token);
  }

  /**
   * Get token TTL in seconds
   */
  getTokenTTL(token: string): number {
    const jwt = parseJWT(token);
    if (!jwt) return 0;

    const now = Math.floor(Date.now() / 1000);
    return Math.max(0, jwt.payload.exp - now);
  }

  /**
   * Sign JWT token
   */
  private async signToken(
    header: JWTHeader,
    payload: JWTPayload,
    signingKey: CryptoKey
  ): Promise<string> {
    const headerB64 = base64URLEncodeJSON(header);
    const payloadB64 = base64URLEncodeJSON(payload);
    const signingInput = `${headerB64}.${payloadB64}`;

    const signature = await crypto.subtle.sign(
      'HMAC',
      signingKey,
      new TextEncoder().encode(signingInput)
    );

    return base64URLEncode(signature);
  }

  /**
   * Verify JWT signature
   */
  private async verifySignature(jwt: JWT, token: string): Promise<boolean> {
    const parts = token.split('.');
    if (parts.length !== 3) return false;

    const [headerB64, payloadB64, signatureB64] = parts;
    const signingInput = `${headerB64}.${payloadB64}`;

    // Get verification key (try current and previous keys for rotation)
    const keyId = jwt.header.kid;
    let verifyingKey: CryptoKey | null = null;

    if (keyId) {
      verifyingKey = await keyManager.getKey(keyId);
    }

    // Fallback to active key if specific key not found
    if (!verifyingKey) {
      const activeKey = await keyManager.getActiveKey();
      verifyingKey = activeKey?.key || null;
    }

    if (!verifyingKey) {
      return false;
    }

    try {
      const signatureBuffer = new TextEncoder().encode(signingInput);
      const signature = new Uint8Array(Array.from(signatureB64).map((c) => c.charCodeAt(0))).buffer;

      return await crypto.subtle.verify('HMAC', verifyingKey, signature, signatureBuffer);
    } catch (error) {
      console.error('Signature verification failed:', error);
      return false;
    }
  }

  /**
   * Ensure service is initialized
   */
  private ensureInitialized(): void {
    if (!this.isInitialized) {
      throw new Error('JWT service not initialized. Call initialize() first.');
    }
  }

  /**
   * Log security events
   */
  private logSecurityEvent(_type: string, _metadata: Record<string, unknown>): void {
    // Security events logged - could be sent to monitoring system
    // console.log('[JWTService]', _type, { ..._metadata, timestamp: new Date().toISOString() })
    // In production, send to security monitoring system
    // securityMonitor.logJWTEvent({ type: _type, metadata: _metadata })
  }
}

export const jwtService = new JWTServiceImpl();
export default jwtService;
