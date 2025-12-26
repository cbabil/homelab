/**
 * Authentication API Service
 * 
 * Handles all authentication-related API calls with secure session management.
 * Now integrated with JWT service for real token-based authentication.
 */

import { 
  LoginCredentials, 
  LoginResponse, 
  User 
} from '@/types/auth'
import { sessionService, SessionMetadata } from '../auth/sessionService'
import { authService } from '../auth/authService'

export interface AuthApiConfig {
  baseUrl: string
  timeout: number
  retryAttempts: number
}

export interface SessionCreateRequest {
  credentials: LoginCredentials
  userAgent: string
  ipAddress: string
}

export interface SessionRefreshRequest {
  sessionId: string
  refreshToken: string
}

export interface SessionListResponse {
  sessions: SessionMetadata[]
  total: number
}

const DEFAULT_CONFIG: AuthApiConfig = {
  baseUrl: '/api/auth',
  timeout: 30000,
  retryAttempts: 3
}

class AuthApiService {
  private config: AuthApiConfig

  constructor(config: Partial<AuthApiConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config }
  }

  /**
   * Authenticate user and create session with JWT tokens
   */
  async login(request: SessionCreateRequest): Promise<LoginResponse> {
    const { credentials, userAgent, ipAddress } = request

    try {
      // Use JWT-based authentication service
      const authResponse = await authService.login(credentials)
      
      // Create secure session with JWT token metadata
      const sessionMetadata = await sessionService.createSession({
        userId: authResponse.user.id,
        rememberMe: credentials.rememberMe || false,
        userAgent,
        ipAddress
      })

      this.logAuthEvent('login_success', { 
        userId: authResponse.user.id,
        sessionId: sessionMetadata.sessionId,
        tokenType: 'JWT'
      })

      return {
        ...authResponse,
        sessionId: sessionMetadata.sessionId
      }
    } catch (error) {
      this.logAuthEvent('login_error', { 
        username: credentials.username,
        error: String(error) 
      })
      throw error
    }
  }

  /**
   * Refresh session with new JWT tokens
   */
  async refreshSession(request: SessionRefreshRequest): Promise<LoginResponse> {
    try {
      // Validate current session
      const validation = await sessionService.validateSession()
      
      if (!validation.isValid) {
        throw new Error('Invalid session for refresh')
      }

      // Use JWT-based token refresh
      const refreshedTokens = await authService.refreshToken(request.refreshToken)
      
      // Renew session metadata
      const refreshedSession = await sessionService.renewSession()

      this.logAuthEvent('session_refreshed', { 
        sessionId: refreshedSession.sessionId,
        userId: refreshedSession.userId,
        tokenType: 'JWT'
      })

      return {
        ...refreshedTokens,
        sessionId: refreshedSession.sessionId
      }
    } catch (error) {
      this.logAuthEvent('refresh_error', { 
        sessionId: request.sessionId,
        error: String(error) 
      })
      throw error
    }
  }

  /**
   * Logout and destroy session with JWT token revocation
   */
  async logout(token?: string): Promise<void> {
    try {
      const currentSession = sessionService.getCurrentSession()
      
      // Revoke JWT token if provided
      if (token) {
        await authService.logout(token)
      }
      
      // Destroy session
      if (currentSession) {
        await sessionService.destroySession()
        
        this.logAuthEvent('logout_success', { 
          sessionId: currentSession.sessionId,
          userId: currentSession.userId,
          tokenRevoked: !!token
        })
      }
    } catch (error) {
      this.logAuthEvent('logout_error', { error: String(error) })
      throw error
    }
  }

  /**
   * Validate current session and JWT token
   */
  async validateSession(token?: string): Promise<boolean> {
    try {
      // Validate session metadata
      const sessionValidation = await sessionService.validateSession()
      if (!sessionValidation.isValid) {
        return false
      }

      // Validate JWT token if provided
      if (token) {
        const tokenValid = await authService.validateToken(token)
        if (!tokenValid) {
          this.logAuthEvent('token_validation_failed', { 
            sessionId: sessionValidation.metadata?.sessionId 
          })
          return false
        }
      }

      return true
    } catch (error) {
      this.logAuthEvent('validation_error', { error: String(error) })
      return false
    }
  }

  /**
   * Get current user session info
   */
  async getCurrentSession(): Promise<SessionMetadata | null> {
    try {
      const validation = await sessionService.validateSession()
      return validation.isValid ? validation.metadata || null : null
    } catch (error) {
      this.logAuthEvent('get_session_error', { error: String(error) })
      return null
    }
  }

  /**
   * List user sessions (for session management)
   */
  async listUserSessions(userId: string): Promise<SessionListResponse> {
    try {
      // Mock implementation - in production, fetch from backend
      const currentSession = sessionService.getCurrentSession()
      
      const sessions = currentSession && currentSession.userId === userId 
        ? [currentSession] 
        : []

      return {
        sessions,
        total: sessions.length
      }
    } catch (error) {
      this.logAuthEvent('list_sessions_error', { 
        userId, 
        error: String(error) 
      })
      throw error
    }
  }

  /**
   * Terminate specific session
   */
  async terminateSession(sessionId: string): Promise<void> {
    try {
      const currentSession = sessionService.getCurrentSession()
      
      if (currentSession?.sessionId === sessionId) {
        await sessionService.destroySession()
        
        this.logAuthEvent('session_terminated', { 
          sessionId,
          userId: currentSession.userId 
        })
      }
    } catch (error) {
      this.logAuthEvent('terminate_session_error', { 
        sessionId, 
        error: String(error) 
      })
      throw error
    }
  }



  /**
   * Log authentication events for security monitoring
   */
  private logAuthEvent(
    event: string, 
    metadata: Record<string, unknown>
  ): void {
    console.log('[AuthAPI]', event, {
      ...metadata,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent
    })
  }
}

export const authApi = new AuthApiService()
export default authApi