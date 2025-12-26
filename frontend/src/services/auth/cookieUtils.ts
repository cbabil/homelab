/**
 * Secure Cookie Utilities
 * 
 * Provides secure cookie management for authentication sessions.
 * Implements HTTP-only cookies with security attributes for CSRF protection.
 */

export interface CookieOptions {
  httpOnly?: boolean
  secure?: boolean
  sameSite?: 'strict' | 'lax' | 'none'
  maxAge?: number
  path?: string
  domain?: string
}

export interface SessionCookieConfig {
  name: string
  options: CookieOptions
  maxAge: number
}

// Default secure cookie configuration
export const DEFAULT_SESSION_CONFIG: SessionCookieConfig = {
  name: 'homelab_session',
  options: {
    httpOnly: true,
    secure: true,
    sameSite: 'strict',
    path: '/',
  },
  maxAge: 3600000, // 1 hour in milliseconds
}

class CookieUtilities {
  private readonly isSecureContext: boolean

  constructor() {
    this.isSecureContext = this.checkSecureContext()
  }

  /**
   * Set secure session cookie
   */
  setSessionCookie(
    name: string, 
    value: string, 
    options: Partial<CookieOptions> = {}
  ): void {
    const config = this.buildCookieConfig(options)
    
    try {
      // Note: Browser-side JavaScript cannot set httpOnly cookies
      // This will be handled by the backend API
      this.logSecurityEvent('cookie_set_attempt', { name, secure: config.secure })
      
      if (!config.httpOnly) {
        document.cookie = this.formatCookieString(name, value, config)
      }
    } catch (error) {
      this.logSecurityEvent('cookie_set_error', { name, error: String(error) })
      throw new Error(`Failed to set cookie ${name}: ${error}`)
    }
  }

  /**
   * Get cookie value (only works for non-httpOnly cookies)
   */
  getCookie(name: string): string | null {
    try {
      const value = `; ${document.cookie}`
      const parts = value.split(`; ${name}=`)
      
      if (parts.length === 2) {
        return parts.pop()?.split(';').shift() || null
      }
      
      return null
    } catch (error) {
      this.logSecurityEvent('cookie_get_error', { name, error: String(error) })
      return null
    }
  }

  /**
   * Delete cookie by setting expiration date in past
   */
  deleteCookie(name: string, options: Partial<CookieOptions> = {}): void {
    try {
      const config = { ...options, maxAge: -1 }
      document.cookie = this.formatCookieString(name, '', config)
      
      this.logSecurityEvent('cookie_deleted', { name })
    } catch (error) {
      this.logSecurityEvent('cookie_delete_error', { name, error: String(error) })
    }
  }

  /**
   * Validate cookie security configuration
   */
  validateCookieConfig(config: CookieOptions): boolean {
    const errors: string[] = []

    if (!config.httpOnly) {
      errors.push('Cookie should be httpOnly for security')
    }

    if (!config.secure && this.isSecureContext) {
      errors.push('Cookie should be secure in HTTPS context')
    }

    if (config.sameSite !== 'strict') {
      errors.push('Cookie should use sameSite=strict for CSRF protection')
    }

    return errors.length === 0
  }

  /**
   * Generate secure session ID
   */
  generateSessionId(): string {
    const timestamp = Date.now().toString(36)
    const randomBytes = crypto.getRandomValues(new Uint8Array(16))
    const randomString = Array.from(randomBytes, byte => 
      byte.toString(16).padStart(2, '0')
    ).join('')
    
    return `${timestamp}-${randomString}`
  }

  /**
   * Check if running in secure context (HTTPS or localhost)
   */
  private checkSecureContext(): boolean {
    if (typeof window !== 'undefined' && window.location) {
      return (
        window.location.protocol === 'https:' ||
        window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1'
      )
    }
    // Default to secure=true for safety in unknown contexts
    return true
  }

  /**
   * Build cookie configuration with security defaults
   */
  private buildCookieConfig(options: Partial<CookieOptions>): CookieOptions {
    return {
      ...DEFAULT_SESSION_CONFIG.options,
      ...options,
      secure: options.secure ?? this.isSecureContext,
    }
  }

  /**
   * Format cookie string for document.cookie
   */
  private formatCookieString(
    name: string, 
    value: string, 
    options: CookieOptions
  ): string {
    const parts = [`${name}=${encodeURIComponent(value)}`]

    if (options.maxAge !== undefined) {
      if (options.maxAge < 0) {
        parts.push('expires=Thu, 01 Jan 1970 00:00:00 GMT')
      } else {
        const expires = new Date(Date.now() + options.maxAge)
        parts.push(`expires=${expires.toUTCString()}`)
      }
    }

    if (options.path) parts.push(`path=${options.path}`)
    if (options.domain) parts.push(`domain=${options.domain}`)
    if (options.secure) parts.push('secure')
    if (options.sameSite) parts.push(`samesite=${options.sameSite}`)

    return parts.join('; ')
  }

  /**
   * Log security events for monitoring
   */
  private logSecurityEvent(event: string, metadata: Record<string, unknown>): void {
    console.log('[Security]', event, metadata)
    
    // In production, send to security monitoring service
    // securityMonitor.logEvent({ event, metadata, timestamp: new Date() })
  }
}

export const cookieUtils = new CookieUtilities()
export default cookieUtils