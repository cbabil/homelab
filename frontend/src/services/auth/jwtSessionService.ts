/**
 * JWT-Enhanced Session Service
 * 
 * Integrates JWT token system with existing session management,
 * providing secure authentication with real cryptographic tokens.
 */

import type { 
  SessionMetadata, 
  SessionValidationResult, 
  CreateSessionOptions 
} from './sessionService'
import type { JWTGenerationOptions } from '@/types/jwt'
import { JWT_STORAGE_KEYS } from '@/types/jwt'

import { jwtService } from './jwtService'
import { settingsService } from '../settingsService'
// Note: getUserIdFromToken, parseJWT, getTimeToExpiration available from '@/utils/jwtUtils' when needed

/**
 * Enhanced session metadata with JWT integration
 */
export interface JWTSessionMetadata extends SessionMetadata {
  accessToken: string
  refreshToken: string
  tokenExpiry: string
}

/**
 * JWT session validation result
 */
export interface JWTSessionValidationResult extends SessionValidationResult {
  accessToken?: string
  refreshToken?: string
}

/**
 * Create session options with user details
 */
export interface CreateJWTSessionOptions extends CreateSessionOptions {
  username: string
  email: string
  role: 'admin' | 'user'
  preferences?: {
    theme?: 'light' | 'dark'
    language?: string
    notifications?: boolean
  }
}

class JWTSessionService {
  private currentSession: JWTSessionMetadata | null = null
  private timeoutWarningTimer: NodeJS.Timeout | null = null
  private sessionExpiryTimer: NodeJS.Timeout | null = null
  private tokenRefreshTimer: NodeJS.Timeout | null = null

  /**
   * Initialize JWT session service
   */
  async initialize(): Promise<void> {
    await jwtService.initialize()
    
    // Attempt to restore session from storage
    await this.restoreSessionFromStorage()
  }

  /**
   * Create new JWT-based secure session
   */
  async createSession(options: CreateJWTSessionOptions): Promise<JWTSessionMetadata> {
    // Ensure services are initialized
    await this.initialize()
    
    try {
      await settingsService.initialize()
    } catch (error) {
      console.warn('Settings not available, using defaults:', error)
    }

    const sessionId = this.generateSessionId()
    const now = new Date()
    const sessionTimeout = settingsService.getSessionTimeoutMs()
    const expiryTime = new Date(now.getTime() + sessionTimeout)

    // Generate JWT token pair
    const tokenOptions: JWTGenerationOptions = {
      userId: options.userId,
      username: options.username,
      email: options.email,
      role: options.role,
      sessionId,
      ipAddress: options.ipAddress,
      userAgent: options.userAgent,
      tokenType: 'access',
      scope: ['read', 'write'],
      preferences: options.preferences
    }

    const [accessToken, refreshToken] = await Promise.all([
      jwtService.generateToken({ ...tokenOptions, tokenType: 'access' }),
      jwtService.generateToken({ ...tokenOptions, tokenType: 'refresh' })
    ])

    // Determine token expiry (shorter of session timeout or token TTL)
    const accessTokenTTL = jwtService.getTokenTTL(accessToken) * 1000
    const tokenExpiry = new Date(Math.min(expiryTime.getTime(), now.getTime() + accessTokenTTL))

    const metadata: JWTSessionMetadata = {
      sessionId,
      userId: options.userId,
      userAgent: options.userAgent,
      ipAddress: options.ipAddress,
      startTime: now.toISOString(),
      lastActivity: now.toISOString(),
      expiryTime: expiryTime.toISOString(),
      accessToken,
      refreshToken,
      tokenExpiry: tokenExpiry.toISOString()
    }

    try {
      // Store session securely
      await this.storeSessionMetadata(metadata)
      
      // Set up session monitoring
      this.currentSession = metadata
      this.setupSessionTimers(expiryTime, tokenExpiry)
      
      this.logSessionEvent('jwt_session_created', {
        sessionId,
        userId: options.userId,
        rememberMe: options.rememberMe,
        tokenExpiry: tokenExpiry.toISOString()
      })

      return metadata
    } catch (error) {
      this.logSessionEvent('jwt_session_create_error', { error: String(error) })
      throw new Error(`Failed to create JWT session: ${error}`)
    }
  }

  /**
   * Validate current JWT session
   */
  async validateSession(): Promise<JWTSessionValidationResult> {
    try {
      const metadata = await this.getSessionMetadata()
      
      if (!metadata) {
        return { isValid: false, reason: 'No session found' }
      }

      // Validate access token
      const tokenValidation = await jwtService.validateToken(metadata.accessToken)
      
      if (!tokenValidation.isValid) {
        // Token invalid, try to refresh
        const refreshResult = await this.attemptTokenRefresh(metadata)
        
        if (refreshResult.success && refreshResult.metadata) {
          return {
            isValid: true,
            metadata: refreshResult.metadata,
            accessToken: refreshResult.metadata.accessToken,
            refreshToken: refreshResult.metadata.refreshToken
          }
        }
        
        // Refresh failed, session invalid
        await this.destroySession()
        return { 
          isValid: false, 
          reason: `Token validation failed: ${tokenValidation.error?.message}` 
        }
      }

      // Check session expiry
      const now = new Date()
      const sessionExpiry = new Date(metadata.expiryTime)
      
      if (sessionExpiry <= now) {
        await this.destroySession()
        return { isValid: false, reason: 'Session expired' }
      }

      // Update last activity
      metadata.lastActivity = now.toISOString()
      await this.storeSessionMetadata(metadata)
      
      this.currentSession = metadata
      return { 
        isValid: true, 
        metadata,
        accessToken: metadata.accessToken,
        refreshToken: metadata.refreshToken
      }
    } catch (error) {
      this.logSessionEvent('jwt_session_validation_error', { error: String(error) })
      return { isValid: false, reason: 'Validation failed' }
    }
  }

  /**
   * Renew session with new tokens
   */
  async renewSession(): Promise<JWTSessionMetadata> {
    const current = await this.getSessionMetadata()
    
    if (!current) {
      throw new Error('No active session to renew')
    }

    try {
      // Refresh tokens using refresh token
      const tokenPair = await jwtService.refreshToken(current.refreshToken)
      
      const now = new Date()
      const sessionTimeout = settingsService.getSessionTimeoutMs()
      const newExpiry = new Date(now.getTime() + sessionTimeout)
      const tokenExpiry = new Date(now.getTime() + (tokenPair.expiresIn * 1000))

      const renewed: JWTSessionMetadata = {
        ...current,
        lastActivity: now.toISOString(),
        expiryTime: newExpiry.toISOString(),
        accessToken: tokenPair.accessToken,
        refreshToken: tokenPair.refreshToken,
        tokenExpiry: tokenExpiry.toISOString()
      }

      await this.storeSessionMetadata(renewed)
      this.currentSession = renewed
      this.setupSessionTimers(newExpiry, tokenExpiry)

      this.logSessionEvent('jwt_session_renewed', {
        sessionId: current.sessionId,
        newExpiry: newExpiry.toISOString(),
        tokenExpiry: tokenExpiry.toISOString()
      })

      return renewed
    } catch (error) {
      this.logSessionEvent('jwt_session_renewal_failed', { 
        error: String(error),
        sessionId: current.sessionId
      })
      throw error
    }
  }

  /**
   * Destroy current session and revoke tokens
   */
  async destroySession(): Promise<void> {
    const sessionId = this.currentSession?.sessionId

    try {
      // Revoke tokens if they exist
      if (this.currentSession?.accessToken) {
        await jwtService.revokeToken(this.currentSession.accessToken, 'logout')
      }
      
      if (this.currentSession?.refreshToken) {
        await jwtService.revokeToken(this.currentSession.refreshToken, 'logout')
      }
      
      // Clear session metadata
      await this.clearSessionMetadata()
      
      // Clear timers
      this.clearSessionTimers()
      
      // Clear current session
      this.currentSession = null

      this.logSessionEvent('jwt_session_destroyed', { sessionId })
    } catch (error) {
      this.logSessionEvent('jwt_session_destroy_error', {
        sessionId,
        error: String(error)
      })
      throw error
    }
  }

  /**
   * Get current session metadata
   */
  getCurrentSession(): JWTSessionMetadata | null {
    return this.currentSession ? { ...this.currentSession } : null
  }

  /**
   * Get current access token
   */
  getAccessToken(): string | null {
    return this.currentSession?.accessToken || null
  }

  /**
   * Get current refresh token
   */
  getRefreshToken(): string | null {
    return this.currentSession?.refreshToken || null
  }

  /**
   * Check if session is close to expiry
   */
  getTimeToExpiry(): number {
    if (!this.currentSession) return 0
    
    const now = new Date()
    const tokenExpiry = new Date(this.currentSession.tokenExpiry)
    const sessionExpiry = new Date(this.currentSession.expiryTime)
    
    // Return time to nearest expiry
    const tokenTime = Math.max(0, tokenExpiry.getTime() - now.getTime())
    const sessionTime = Math.max(0, sessionExpiry.getTime() - now.getTime())
    
    return Math.min(tokenTime, sessionTime)
  }

  /**
   * Record user activity
   */
  recordActivity(): void {
    if (!this.currentSession) return

    const now = new Date().toISOString()
    this.currentSession.lastActivity = now
    
    // Persist updated activity
    this.storeSessionMetadata(this.currentSession).catch(error => {
      console.error('Failed to update session activity:', error)
    })
  }

  /**
   * Attempt to refresh tokens automatically
   */
  private async attemptTokenRefresh(metadata: JWTSessionMetadata): Promise<{
    success: boolean
    metadata?: JWTSessionMetadata
  }> {
    try {
      const tokenPair = await jwtService.refreshToken(metadata.refreshToken)
      
      const now = new Date()
      const tokenExpiry = new Date(now.getTime() + (tokenPair.expiresIn * 1000))
      
      const refreshedMetadata: JWTSessionMetadata = {
        ...metadata,
        lastActivity: now.toISOString(),
        accessToken: tokenPair.accessToken,
        refreshToken: tokenPair.refreshToken,
        tokenExpiry: tokenExpiry.toISOString()
      }
      
      await this.storeSessionMetadata(refreshedMetadata)
      this.currentSession = refreshedMetadata
      
      return { success: true, metadata: refreshedMetadata }
    } catch (error) {
      this.logSessionEvent('token_refresh_failed', { error: String(error) })
      return { success: false }
    }
  }

  /**
   * Store session metadata securely
   */
  private async storeSessionMetadata(metadata: JWTSessionMetadata): Promise<void> {
    try {
      // Store tokens securely in localStorage
      localStorage.setItem(JWT_STORAGE_KEYS.ACCESS_TOKEN, metadata.accessToken)
      localStorage.setItem(JWT_STORAGE_KEYS.REFRESH_TOKEN, metadata.refreshToken)
      
      // Store non-sensitive session metadata
      const sessionData = {
        sessionId: metadata.sessionId,
        userId: metadata.userId,
        userAgent: metadata.userAgent,
        ipAddress: metadata.ipAddress,
        startTime: metadata.startTime,
        lastActivity: metadata.lastActivity,
        expiryTime: metadata.expiryTime,
        tokenExpiry: metadata.tokenExpiry
      }
      
      const encrypted = btoa(JSON.stringify(sessionData))
      localStorage.setItem(`session_${metadata.sessionId}`, encrypted)
      localStorage.setItem('current_session_id', metadata.sessionId)
    } catch (error) {
      throw new Error(`Failed to store JWT session: ${error}`)
    }
  }

  /**
   * Get session metadata from storage
   */
  private async getSessionMetadata(): Promise<JWTSessionMetadata | null> {
    try {
      const currentSessionId = localStorage.getItem('current_session_id')
      if (!currentSessionId) return null

      const encrypted = localStorage.getItem(`session_${currentSessionId}`)
      const accessToken = localStorage.getItem(JWT_STORAGE_KEYS.ACCESS_TOKEN)
      const refreshToken = localStorage.getItem(JWT_STORAGE_KEYS.REFRESH_TOKEN)

      if (!encrypted || !accessToken || !refreshToken) return null

      const sessionData = JSON.parse(atob(encrypted))
      
      return {
        ...sessionData,
        accessToken,
        refreshToken
      } as JWTSessionMetadata
    } catch (error) {
      console.error('Failed to get JWT session metadata:', error)
      return null
    }
  }

  /**
   * Clear session metadata from storage
   */
  private async clearSessionMetadata(): Promise<void> {
    try {
      const currentSessionId = this.currentSession?.sessionId || 
                               localStorage.getItem('current_session_id')
      
      if (currentSessionId) {
        localStorage.removeItem(`session_${currentSessionId}`)
      }
      
      localStorage.removeItem('current_session_id')
      localStorage.removeItem(JWT_STORAGE_KEYS.ACCESS_TOKEN)
      localStorage.removeItem(JWT_STORAGE_KEYS.REFRESH_TOKEN)
    } catch (error) {
      console.error('Failed to clear JWT session metadata:', error)
      throw error
    }
  }

  /**
   * Restore session from storage on initialization
   */
  private async restoreSessionFromStorage(): Promise<void> {
    try {
      const metadata = await this.getSessionMetadata()
      if (!metadata) return

      // Validate the restored session
      const validation = await this.validateSession()
      if (validation.isValid && validation.metadata) {
        this.currentSession = validation.metadata as JWTSessionMetadata
        
        const sessionExpiry = new Date(this.currentSession.expiryTime)
        const tokenExpiry = new Date(this.currentSession.tokenExpiry)
        this.setupSessionTimers(sessionExpiry, tokenExpiry)
      }
    } catch (error) {
      console.warn('Failed to restore session from storage:', error)
      await this.clearSessionMetadata()
    }
  }

  /**
   * Setup session and token refresh timers
   */
  private setupSessionTimers(sessionExpiry: Date, tokenExpiry: Date): void {
    this.clearSessionTimers()

    const now = new Date()
    const timeToSessionExpiry = sessionExpiry.getTime() - now.getTime()
    const timeToTokenExpiry = tokenExpiry.getTime() - now.getTime()

    // Set token refresh timer (refresh 5 minutes before expiry)
    const refreshTime = timeToTokenExpiry - (5 * 60 * 1000)
    if (refreshTime > 0) {
      this.tokenRefreshTimer = setTimeout(async () => {
        try {
          await this.renewSession()
        } catch (error) {
          console.error('Automatic token refresh failed:', error)
          await this.destroySession()
        }
      }, refreshTime)
    }

    // Set session expiry timer
    if (timeToSessionExpiry > 0) {
      this.sessionExpiryTimer = setTimeout(() => {
        this.destroySession()
      }, timeToSessionExpiry)
    }

    // Set warning timer
    const settings = settingsService.getSettings()
    const warningTime = settings.security.session.showWarningMinutes * 60 * 1000
    const timeToWarning = Math.min(timeToSessionExpiry, timeToTokenExpiry) - warningTime

    if (timeToWarning > 0) {
      this.timeoutWarningTimer = setTimeout(() => {
        this.showSessionWarning()
      }, timeToWarning)
    }
  }

  /**
   * Clear all session timers
   */
  private clearSessionTimers(): void {
    if (this.timeoutWarningTimer) {
      clearTimeout(this.timeoutWarningTimer)
      this.timeoutWarningTimer = null
    }
    
    if (this.sessionExpiryTimer) {
      clearTimeout(this.sessionExpiryTimer)
      this.sessionExpiryTimer = null
    }

    if (this.tokenRefreshTimer) {
      clearTimeout(this.tokenRefreshTimer)
      this.tokenRefreshTimer = null
    }
  }

  /**
   * Show session timeout warning
   */
  private showSessionWarning(): void {
    const timeRemaining = this.getTimeToExpiry()
    const minutesRemaining = Math.ceil(timeRemaining / (60 * 1000))

    this.logSessionEvent('jwt_session_warning_shown', {
      minutesRemaining,
      sessionId: this.currentSession?.sessionId
    })

    console.warn(`JWT session expires in ${minutesRemaining} minutes`)
  }

  /**
   * Generate unique session ID
   */
  private generateSessionId(): string {
    const timestamp = Date.now().toString(36)
    const random = Math.random().toString(36).substring(2)
    return `jwt_session_${timestamp}_${random}`
  }

  /**
   * Log session events
   */
  private logSessionEvent(_event: string, _metadata: Record<string, unknown>): void {
    // Session events logged - could be sent to monitoring service
    // console.log('[JWTSession]', _event, { ..._metadata, timestamp: new Date().toISOString(), userAgent: navigator.userAgent })
  }
}

export const jwtSessionService = new JWTSessionService()
export default jwtSessionService