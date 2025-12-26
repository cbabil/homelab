/**
 * JWT Types and Interfaces
 * 
 * Comprehensive type definitions for JWT token system including
 * payload structure, token pairs, security metadata, and configuration.
 */

// Standard JWT Claims (RFC 7519)
export interface JWTStandardClaims {
  iss: string       // Issuer
  sub: string       // Subject (user ID)
  aud: string       // Audience
  exp: number       // Expiration time (Unix timestamp)
  iat: number       // Issued at (Unix timestamp)
  jti: string       // JWT ID (unique token identifier)
}

// User-specific claims in JWT payload
export interface JWTUserClaims {
  id: string
  username: string
  email: string
  role: 'admin' | 'user'
  preferences?: {
    theme?: 'light' | 'dark'
    language?: string
    notifications?: boolean
  }
}

// Session context claims for security tracking
export interface JWTSessionClaims {
  sessionId: string
  ipAddress: string
  userAgent: string
  startTime: number     // Unix timestamp
  lastActivity: number  // Unix timestamp
}

// Security metadata claims
export interface JWTSecurityClaims {
  tokenType: 'access' | 'refresh'
  scope: string[]
  authMethod: 'password' | 'refresh'
  riskLevel: 'low' | 'medium' | 'high'
}

// Complete JWT payload structure
export interface JWTPayload extends 
  JWTStandardClaims, 
  JWTUserClaims, 
  JWTSessionClaims, 
  JWTSecurityClaims {}

// JWT Header structure
export interface JWTHeader {
  alg: 'HS256'      // Algorithm (HS256 only for security)
  typ: 'JWT'        // Type
  kid?: string      // Key ID for key rotation
}

// Complete JWT structure
export interface JWT {
  header: JWTHeader
  payload: JWTPayload
  signature: string
}

// Token pair for access/refresh pattern
export interface TokenPair {
  accessToken: string
  refreshToken: string
  expiresIn: number        // Access token expiry in seconds
  refreshExpiresIn: number // Refresh token expiry in seconds
}

// JWT validation result
export interface JWTValidationResult {
  isValid: boolean
  payload?: JWTPayload
  error?: JWTValidationError
}

// JWT validation errors
export interface JWTValidationError {
  code: 'EXPIRED' | 'INVALID_SIGNATURE' | 'MALFORMED' | 
        'ALGORITHM_MISMATCH' | 'AUDIENCE_MISMATCH' | 
        'ISSUER_MISMATCH' | 'NOT_YET_VALID' | 'REVOKED'
  message: string
  details?: Record<string, unknown>
}

// JWT generation options
export interface JWTGenerationOptions {
  userId: string
  username: string
  email: string
  role: 'admin' | 'user'
  sessionId: string
  ipAddress: string
  userAgent: string
  tokenType: 'access' | 'refresh'
  scope?: string[]
  preferences?: JWTUserClaims['preferences']
  customClaims?: Record<string, unknown>
}

// JWT configuration
export interface JWTConfig {
  issuer: string
  audience: string
  accessTokenTTL: number    // seconds
  refreshTokenTTL: number   // seconds
  clockTolerance: number    // seconds for exp/nbf validation
  algorithm: 'HS256'
  keyRotationInterval: number // hours
}

// Key management interfaces
export interface CryptoKeyInfo {
  id: string
  algorithm: string
  usage: KeyUsage[]
  createdAt: number
  expiresAt?: number
  isActive: boolean
}

// Secure key storage interface
export interface SecureKeyStorage {
  storeKey(keyId: string, key: CryptoKey): Promise<void>
  getKey(keyId: string): Promise<CryptoKey | null>
  listKeys(): Promise<CryptoKeyInfo[]>
  deleteKey(keyId: string): Promise<void>
  rotateKeys(): Promise<string> // Returns new active key ID
}

// Token blacklist entry
export interface BlacklistEntry {
  jti: string              // JWT ID
  exp: number              // Expiration time
  reason: 'logout' | 'revoke' | 'security'
  timestamp: number        // Blacklist entry creation time
}

// Token blacklist interface
export interface TokenBlacklist {
  add(entry: BlacklistEntry): Promise<void>
  isBlacklisted(jti: string): Promise<boolean>
  cleanup(): Promise<void>  // Remove expired entries
}

// JWT service interface
export interface JWTService {
  generateToken(options: JWTGenerationOptions): Promise<string>
  validateToken(token: string): Promise<JWTValidationResult>
  refreshToken(refreshToken: string): Promise<TokenPair>
  revokeToken(token: string, reason: BlacklistEntry['reason']): Promise<void>
  decodeToken(token: string): JWT | null
  getTokenTTL(token: string): number
}

// Default JWT configuration
export const DEFAULT_JWT_CONFIG: JWTConfig = {
  issuer: 'homelab-auth-service',
  audience: 'homelab-frontend',
  accessTokenTTL: 3600,      // 1 hour
  refreshTokenTTL: 604800,   // 7 days
  clockTolerance: 30,        // 30 seconds
  algorithm: 'HS256',
  keyRotationInterval: 168   // 7 days
}

// JWT storage keys
export const JWT_STORAGE_KEYS = {
  ACCESS_TOKEN: 'homelab-jwt-access',
  REFRESH_TOKEN: 'homelab-jwt-refresh',
  KEY_STORAGE: 'homelab-jwt-keys',
  BLACKLIST: 'homelab-jwt-blacklist',
  CONFIG: 'homelab-jwt-config'
} as const

// JWT security events
export interface JWTSecurityEvent {
  type: 'token_generated' | 'token_validated' | 'token_expired' | 
        'token_revoked' | 'invalid_signature' | 'key_rotated'
  timestamp: number
  tokenId?: string
  userId?: string
  details?: Record<string, unknown>
}