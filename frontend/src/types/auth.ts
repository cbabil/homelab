/**
 * Authentication Types
 * 
 * Comprehensive type definitions for authentication system including
 * user models, login credentials, auth state, JWT integration, and form validation.
 */

import type { JWTPayload, JWTValidationResult } from './jwt'

// User model representing authenticated user data
export interface User {
  id: string
  username: string
  email?: string  // Optional - not required for registration
  role: 'admin' | 'user'
  lastLogin: string
  isActive: boolean
  createdAt?: string
  preferences?: {
    theme?: 'light' | 'dark'
    language?: string
    notifications?: boolean
  }
}

// Login credentials for authentication
export interface LoginCredentials {
  username: string
  password: string
  rememberMe?: boolean
}

// Registration credentials for new user creation
export interface RegistrationCredentials {
  username: string
  email: string
  password: string
  confirmPassword: string
  role?: 'admin' | 'user'  // Default: 'user'
  acceptTerms: boolean
}

// Session activity tracking
export interface SessionActivity {
  lastActivity: string
  isIdle: boolean
  idleDuration: number // milliseconds
  activityCount: number
}

// Session warning state
export interface SessionWarning {
  isShowing: boolean
  minutesRemaining: number
  warningLevel: 'info' | 'warning' | 'critical'
}

// Enhanced authentication state with session management and JWT support
export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  sessionExpiry: string | null
  activity: SessionActivity | null
  warning: SessionWarning | null
  tokenType?: 'JWT' | 'Bearer'
  tokenExpiry?: string | null
  tokenMetadata?: Partial<JWTPayload>
}

// Login response from authentication API
export interface LoginResponse {
  user: User
  token: string
  refreshToken?: string
  expiresIn: number
  sessionId?: string
  tokenType?: 'JWT' | 'Bearer'
}

// Registration response
export interface RegistrationResponse extends LoginResponse {
  isEmailVerified: boolean
  verificationToken?: string
}

// JWT-enhanced login response with token metadata
export interface JWTLoginResponse extends LoginResponse {
  tokenType: 'JWT'
  tokenPayload?: JWTPayload
  refreshExpiresIn?: number
}

// Authentication error types
export interface AuthError {
  code: string
  message: string
  field?: string
}

// JWT-specific error types
export interface JWTAuthError extends AuthError {
  tokenError?: JWTValidationResult['error']
  tokenId?: string
  userId?: string
}

// Form validation state for login form
export interface LoginFormState {
  username: {
    value: string
    error?: string
    isValid: boolean
  }
  password: {
    value: string
    error?: string
    isValid: boolean
  }
  rememberMe: boolean
  isSubmitting: boolean
  submitError?: string
}

// Registration form state (mirrors LoginFormState pattern)
export interface RegistrationFormState {
  username: {
    value: string
    error?: string
    isValid: boolean
  }
  email: {
    value: string
    error?: string
    isValid: boolean
  }
  password: {
    value: string
    error?: string
    isValid: boolean
    strength?: PasswordStrength
  }
  confirmPassword: {
    value: string
    error?: string
    isValid: boolean
  }
  acceptTerms: {
    value: boolean
    error?: string
    isValid: boolean
  }
  isSubmitting: boolean
  submitError?: string
}

// Password validation criteria
export interface PasswordValidation {
  minLength: boolean
  hasUppercase: boolean
  hasLowercase: boolean
  hasNumber: boolean
  hasSpecialChar: boolean
  isValid: boolean
}

// Password strength for registration (not login) - Legacy mode
export interface PasswordStrength {
  score: number // 0-5
  feedback: string[]
  requirements: {
    minLength: boolean
    hasUppercase: boolean
    hasLowercase: boolean
    hasNumber: boolean
    hasSpecialChar: boolean
  }
}

// Session storage keys for persistence
export const AUTH_STORAGE_KEYS = {
  TOKEN: 'tomo-auth-token',
  REFRESH_TOKEN: 'tomo-refresh-token',
  USER: 'tomo-user-data',
  REMEMBER_ME: 'tomo-remember-me',
  SESSION_EXPIRY: 'tomo-session-expiry',
  LAST_ACTIVITY: 'tomo-last-activity',
  ACTIVITY_COUNT: 'tomo-activity-count',
  TOKEN_TYPE: 'tomo-token-type',
  TOKEN_EXPIRY: 'tomo-token-expiry',
  TOKEN_METADATA: 'tomo-token-metadata'
} as const

// Authentication context interface with JWT support
export interface AuthContextType {
  // State
  authState: AuthState
  
  // Actions
  login: (credentials: LoginCredentials) => Promise<void>
  register: (credentials: RegistrationCredentials) => Promise<void>
  logout: () => void
  refreshSession: () => Promise<void>
  
  // Session management
  recordActivity: () => void
  dismissWarning: () => void
  extendSession: () => Promise<void>
  
  // JWT-specific methods
  validateToken: (token?: string) => Promise<boolean>
  getTokenMetadata: () => Partial<JWTPayload> | null
  isTokenExpired: () => boolean
  
  // Utilities
  isAuthenticated: boolean
  isLoading: boolean
  user: User | null
  error: string | null
  activity: SessionActivity | null
  warning: SessionWarning | null
  tokenType: 'JWT' | 'Bearer' | null
  tokenExpiry: string | null
}

// Route protection configuration
export interface ProtectedRouteConfig {
  requireAuth: boolean
  redirectTo?: string
  allowedRoles?: User['role'][]
}

// Login form validation rules
export interface LoginValidationRules {
  username: {
    required: boolean
    minLength?: number
    pattern?: RegExp
  }
  password: {
    required: boolean
    minLength?: number
    maxLength?: number
    complexity?: {
      requireUppercase: boolean
      requireLowercase: boolean
      requireNumbers: boolean
      requireSpecialChars: boolean
    }
  }
}

// Default validation rules for login (simplified - no complexity requirements)
export const DEFAULT_LOGIN_VALIDATION: LoginValidationRules = {
  username: {
    required: true,
    minLength: 3
  },
  password: {
    required: true
  }
}

// Registration validation rules (comprehensive for new users)
export interface RegistrationValidationRules {
  username: {
    required: boolean
    minLength: number
    maxLength: number
    pattern?: RegExp
  }
  email: {
    required: boolean
    maxLength: number
    pattern: RegExp
  }
  password: {
    required: boolean
    minLength: number
    maxLength: number
    complexity: {
      requireUppercase: boolean
      requireLowercase: boolean
      requireNumbers: boolean
      requireSpecialChars: boolean
    }
  }
  confirmPassword: {
    required: boolean
    mustMatch: boolean
  }
  acceptTerms: {
    required: boolean
  }
}

// Default validation rules for registration (secure requirements)
export const DEFAULT_REGISTRATION_VALIDATION: RegistrationValidationRules = {
  username: {
    required: true,
    minLength: 3,
    maxLength: 50,
    pattern: /^[a-zA-Z0-9_-]+$/
  },
  email: {
    required: true,
    maxLength: 254,
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  },
  password: {
    required: true,
    minLength: 12,
    maxLength: 128,
    complexity: {
      requireUppercase: true,
      requireLowercase: true,
      requireNumbers: true,
      requireSpecialChars: true
    }
  },
  confirmPassword: {
    required: true,
    mustMatch: true
  },
  acceptTerms: {
    required: true
  }
}

// Authentication events for tracking
export interface AuthEvent {
  type: 'login' | 'logout' | 'refresh' | 'error' | 'token_validation' | 'token_refresh'
  timestamp: string
  userId?: string
  tokenType?: 'JWT' | 'Bearer'
  tokenId?: string
  metadata?: Record<string, unknown>
}

// JWT-specific authentication events
export interface JWTAuthEvent extends AuthEvent {
  tokenType: 'JWT'
  tokenId: string
  tokenExpiry?: string
  refreshTokenId?: string
  validationResult?: JWTValidationResult
}

// Session security configuration
export interface SessionSecurityConfig {
  cookieName: string
  httpOnly: boolean
  secure: boolean
  sameSite: 'strict' | 'lax' | 'none'
  maxAge: number
  path: string
}

// Secure session data (stored server-side, referenced by cookie)
export interface SecureSession {
  sessionId: string
  userId: string
  userAgent: string
  ipAddress: string
  startTime: string
  lastActivity: string
  expiryTime: string
  isActive: boolean
  tokenType?: 'JWT' | 'Bearer'
  tokenExpiry?: string
  refreshTokenExpiry?: string
}

// JWT-enhanced secure session
export interface JWTSecureSession extends SecureSession {
  tokenType: 'JWT'
  accessTokenId: string
  refreshTokenId: string
  tokenExpiry: string
  refreshTokenExpiry: string
  scope: string[]
  lastTokenRefresh?: string
}

// JWT-enhanced auth context with token management
export interface JWTAuthContextType extends AuthContextType {
  // JWT-specific state
  tokenPayload: JWTPayload | null
  refreshTokenExpiry: string | null
  
  // JWT-specific actions
  refreshTokens: () => Promise<void>
  revokeToken: (token?: string) => Promise<void>
  decodeToken: (token?: string) => JWTPayload | null
  
  // Token timing utilities
  getTokenTimeRemaining: () => number
  shouldRefreshToken: () => boolean
}

// Cookie-based auth context (no sensitive data in client storage)
export interface CookieAuthContextType {
  // State
  authState: AuthState
  
  // Actions
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
  refreshSession: () => Promise<void>
  
  // Session management
  recordActivity: () => void
  dismissWarning: () => void
  extendSession: () => Promise<void>
  getCurrentSession: () => SecureSession | null
  
  // JWT validation
  validateToken: (token?: string) => Promise<boolean>
  
  // Utilities
  isAuthenticated: boolean
  isLoading: boolean
  user: User | null
  error: string | null
  activity: SessionActivity | null
  warning: SessionWarning | null
  tokenType: 'JWT' | 'Bearer' | null
}