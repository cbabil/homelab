/**
 * Secure Session Service
 * 
 * Manages secure cookie-based sessions with JWT token integration.
 * Handles validation, renewal, and timeout with real JWT tokens.
 */

import { cookieUtils, DEFAULT_SESSION_CONFIG } from './cookieUtils'
import { settingsService } from '../settingsService'
import { jwtService } from './jwtService'

export interface SessionMetadata {
  sessionId: string
  userId: string
  userAgent: string
  ipAddress: string
  startTime: string
  lastActivity: string
  expiryTime: string
  accessToken?: string
  refreshToken?: string
  tokenExpiry?: string
}

export interface SessionValidationResult {
  isValid: boolean
  reason?: string
  metadata?: SessionMetadata
}

export interface CreateSessionOptions {
  userId: string
  rememberMe: boolean
  userAgent: string
  ipAddress: string
}

class SessionService {
  private readonly sessionCookieName = DEFAULT_SESSION_CONFIG.name
  private currentSession: SessionMetadata | null = null
  private timeoutWarningTimer: NodeJS.Timeout | null = null
  private sessionExpiryTimer: NodeJS.Timeout | null = null
  private isInitialized = false

  /**
   * Initialize session service
   */
  async initialize(): Promise<void> {
    if (!this.isInitialized) {
      await jwtService.initialize()
      this.isInitialized = true
    }
  }

  /**
   * Create new secure session with JWT token integration
   */
  async createSession(options: CreateSessionOptions): Promise<SessionMetadata> {
    await this.ensureInitialized()
    
    // Ensure settings service is initialized
    try {
      await settingsService.initialize()
    } catch (error) {
      console.warn('Settings not available, using defaults:', error)
    }

    const sessionId = cookieUtils.generateSessionId()
    const now = new Date()
    const sessionTimeout = settingsService.getSessionTimeoutMs()
    const expiryTime = new Date(now.getTime() + sessionTimeout)

    const metadata: SessionMetadata = {
      sessionId,
      userId: options.userId,
      userAgent: options.userAgent,
      ipAddress: options.ipAddress,
      startTime: now.toISOString(),
      lastActivity: now.toISOString(),
      expiryTime: expiryTime.toISOString()
    }

    try {
      // Store session metadata
      await this.storeSessionMetadata(metadata)
      
      // Set up session monitoring
      this.currentSession = metadata
      this.setupSessionTimers(expiryTime)
      
      this.logSessionEvent('session_created', { 
        sessionId, 
        userId: options.userId,
        rememberMe: options.rememberMe,
        jwtEnabled: true
      })

      return metadata
    } catch (error) {
      this.logSessionEvent('session_create_error', { error: String(error) })
      throw new Error(`Failed to create session: ${error}`)
    }
  }

  /**
   * Validate current session with JWT token validation
   */
  async validateSession(token?: string): Promise<SessionValidationResult> {
    await this.ensureInitialized()
    
    try {
      const metadata = await this.getSessionMetadata()
      
      if (!metadata) {
        return { isValid: false, reason: 'Authentication required' }
      }

      const now = new Date()
      const expiryTime = new Date(metadata.expiryTime)

      if (expiryTime <= now) {
        await this.destroySession()
        return { isValid: false, reason: 'Authentication required' }
      }

      // Validate JWT token if provided or stored
      const tokenToValidate = token || metadata.accessToken
      if (tokenToValidate) {
        const tokenValidation = await jwtService.validateToken(tokenToValidate)
        if (!tokenValidation.isValid) {
          this.logSessionEvent('jwt_validation_failed', {
            sessionId: metadata.sessionId,
            error: tokenValidation.error?.message
          })
          await this.destroySession()
          return { 
            isValid: false, 
            reason: 'Authentication required' 
          }
        }
      }

      // Update last activity
      metadata.lastActivity = now.toISOString()
      await this.storeSessionMetadata(metadata)
      
      this.currentSession = metadata
      return { isValid: true, metadata }
    } catch (error) {
      this.logSessionEvent('session_validation_error', { error: String(error) })
      return { isValid: false, reason: 'Authentication required' }
    }
  }

  /**
   * Renew session with new expiry and JWT token refresh
   */
  async renewSession(newTokens?: {accessToken: string, refreshToken: string}): Promise<SessionMetadata> {
    await this.ensureInitialized()
    
    const current = await this.getSessionMetadata()
    
    if (!current) {
      throw new Error('No active session to renew')
    }

    const now = new Date()
    const sessionTimeout = settingsService.getSessionTimeoutMs()
    const newExpiry = new Date(now.getTime() + sessionTimeout)

    const renewed: SessionMetadata = {
      ...current,
      lastActivity: now.toISOString(),
      expiryTime: newExpiry.toISOString()
    }

    // Update JWT tokens if provided
    if (newTokens) {
      renewed.accessToken = newTokens.accessToken
      renewed.refreshToken = newTokens.refreshToken
      
      // Calculate token expiry from JWT
      const decodedToken = jwtService.decodeToken(newTokens.accessToken)
      if (decodedToken?.payload?.exp) {
        renewed.tokenExpiry = new Date(decodedToken.payload.exp * 1000).toISOString()
      }
    }

    await this.storeSessionMetadata(renewed)
    this.currentSession = renewed
    this.setupSessionTimers(newExpiry)

    this.logSessionEvent('session_renewed', { 
      sessionId: current.sessionId,
      newExpiry: newExpiry.toISOString(),
      tokensUpdated: !!newTokens
    })

    return renewed
  }

  /**
   * Destroy current session and revoke JWT tokens
   */
  async destroySession(): Promise<void> {
    await this.ensureInitialized()
    
    const sessionId = this.currentSession?.sessionId
    const accessToken = this.currentSession?.accessToken
    const refreshToken = this.currentSession?.refreshToken

    try {
      // Revoke JWT tokens if present
      const revocationPromises = []
      if (accessToken) {
        revocationPromises.push(
          jwtService.revokeToken(accessToken, 'logout').catch(console.error)
        )
      }
      if (refreshToken && refreshToken !== accessToken) {
        revocationPromises.push(
          jwtService.revokeToken(refreshToken, 'logout').catch(console.error)
        )
      }
      
      // Wait for token revocations (but don't fail if they error)
      await Promise.allSettled(revocationPromises)
      
      // Clear session metadata
      await this.clearSessionMetadata()
      
      // Clear timers
      this.clearSessionTimers()
      
      // Clear current session
      this.currentSession = null

      this.logSessionEvent('session_destroyed', { 
        sessionId,
        tokensRevoked: revocationPromises.length > 0
      })
    } catch (error) {
      this.logSessionEvent('session_destroy_error', { 
        sessionId, 
        error: String(error) 
      })
      throw error
    }
  }

  /**
   * Get current session metadata
   */
  getCurrentSession(): SessionMetadata | null {
    return this.currentSession ? { ...this.currentSession } : null
  }

  /**
   * Check if session is close to expiry
   */
  getTimeToExpiry(): number {
    if (!this.currentSession) return 0
    
    const now = new Date()
    const expiry = new Date(this.currentSession.expiryTime)
    return Math.max(0, expiry.getTime() - now.getTime())
  }

  /**
   * Record user activity and validate JWT token expiry
   */
  recordActivity(): void {
    if (!this.currentSession) return

    const now = new Date().toISOString()
    this.currentSession.lastActivity = now
    
    // Check if JWT token needs refresh (if expiring soon)
    if (this.currentSession.tokenExpiry) {
      const tokenExpiry = new Date(this.currentSession.tokenExpiry)
      const timeToExpiry = tokenExpiry.getTime() - Date.now()
      const refreshThreshold = 5 * 60 * 1000 // 5 minutes
      
      if (timeToExpiry < refreshThreshold && timeToExpiry > 0) {
        this.logSessionEvent('token_refresh_needed', {
          sessionId: this.currentSession.sessionId,
          timeToExpiry
        })
      }
    }
    
    // Persist updated activity (debounced in production)
    this.storeSessionMetadata(this.currentSession).catch(error => {
      console.error('Failed to update session activity:', error)
    })
  }

  /**
   * Store session metadata (simulates server-side storage)
   */
  private async storeSessionMetadata(metadata: SessionMetadata): Promise<void> {
    try {
      // In production, this would be stored server-side
      // For demo, we use secure localStorage with encryption simulation
      const encrypted = btoa(JSON.stringify(metadata))
      localStorage.setItem(`session_${metadata.sessionId}`, encrypted)
      localStorage.setItem('current_session_id', metadata.sessionId)
    } catch (error) {
      throw new Error(`Failed to store session: ${error}`)
    }
  }

  /**
   * Get session metadata from storage
   */
  private async getSessionMetadata(): Promise<SessionMetadata | null> {
    try {
      const currentSessionId = localStorage.getItem('current_session_id')
      
      if (!currentSessionId) return null

      const encrypted = localStorage.getItem(`session_${currentSessionId}`)
      
      if (!encrypted) return null

      const decrypted = atob(encrypted)
      return JSON.parse(decrypted) as SessionMetadata
    } catch (error) {
      console.error('Failed to get session metadata:', error)
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
    } catch (error) {
      console.error('Failed to clear session metadata:', error)
      throw error
    }
  }

  /**
   * Setup session timeout and warning timers
   */
  private setupSessionTimers(expiryTime: Date): void {
    this.clearSessionTimers()

    const now = new Date()
    const timeToExpiry = expiryTime.getTime() - now.getTime()
    const settings = settingsService.getSettings()
    const warningTime = settings.security.session.showWarningMinutes * 60 * 1000
    const timeToWarning = timeToExpiry - warningTime

    // Set warning timer
    if (timeToWarning > 0) {
      this.timeoutWarningTimer = setTimeout(() => {
        this.showSessionWarning()
      }, timeToWarning)
    }

    // Set expiry timer
    this.sessionExpiryTimer = setTimeout(() => {
      this.destroySession()
    }, timeToExpiry)
  }

  /**
   * Clear session timers
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
  }

  /**
   * Show session timeout warning
   */
  private showSessionWarning(): void {
    const timeRemaining = this.getTimeToExpiry()
    const minutesRemaining = Math.ceil(timeRemaining / (60 * 1000))

    this.logSessionEvent('session_warning_shown', { 
      minutesRemaining,
      sessionId: this.currentSession?.sessionId 
    })

    // In production, this would trigger UI warning component
    // For now, just log the warning
    console.warn(`Session expires in ${minutesRemaining} minutes`)
  }

  /**
   * Ensure service is initialized
   */
  private async ensureInitialized(): Promise<void> {
    if (!this.isInitialized) {
      await this.initialize()
    }
  }

  /**
   * Log session events for security monitoring
   */
  private logSessionEvent(
    event: string, 
    metadata: Record<string, unknown>
  ): void {
    console.log('[Session]', event, {
      ...metadata,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      jwtIntegration: true
    })
    
    // In production, send to security monitoring
    // securityMonitor.logSessionEvent({ event, metadata })
  }
}

export const sessionService = new SessionService()
export default sessionService