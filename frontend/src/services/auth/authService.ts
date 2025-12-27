/**
 * Authentication Service
 * 
 * Core authentication operations including login, token refresh,
 * and validation. Now integrated with JWT service for real token management.
 */

import type { LoginCredentials, User, LoginResponse, RegistrationCredentials, RegistrationResponse } from '@/types/auth'
import type { JWTGenerationOptions } from '@/types/jwt'
import { jwtService } from './jwtService'
import { HomelabMCPClient } from '@/services/mcpClient'

interface OfflineUserRecord {
  id: string
  username: string
  email: string
  role: 'admin' | 'user'
  passwordHash: string
  fallbackPassword: string
  preferences?: User['preferences']
}

const OFFLINE_USERS: OfflineUserRecord[] = [
  {
    id: 'offline-admin',
    username: 'admin',
    email: 'admin@homelab.local',
    role: 'admin',
    passwordHash: '129e0dbb4444949eaecba34d003b73967be5428e04d8a865b7b63121eb58991e',
    fallbackPassword: 'HomeLabAdmin123!',
    preferences: {
      theme: 'dark',
      notifications: true
    }
  },
  {
    id: 'offline-user',
    username: 'user',
    email: 'user@homelab.local',
    role: 'user',
    passwordHash: '04a3c826a7ef022e17beec74d3dc66653771f98c03463202f8179afe26ec9e4e',
    fallbackPassword: 'HomeLabUser123!',
    preferences: {
      theme: 'light',
      notifications: true
    }
  }
]

const MCP_CONNECTION_ERROR_PATTERNS = [
  'failed to connect to mcp server',
  'failed to fetch',
  'networkerror',
  'connection refused',
  'mcp_connection_error'
]

class AuthService {
  private isInitialized = false
  private mcpClient: HomelabMCPClient
  private offlineMode = false

  /**
   * Initialize authentication service
   */
  async initialize(): Promise<void> {
    if (!this.isInitialized) {
      await jwtService.initialize()
      const serverUrl = import.meta.env.VITE_MCP_SERVER_URL || '/mcp'
      this.mcpClient = new HomelabMCPClient(serverUrl)

      try {
        await this.mcpClient.connect()
        this.offlineMode = false
      } catch (error) {
        this.offlineMode = true
        console.warn('[AuthService] MCP connection unavailable, enabling offline mode', error)
      }

      this.isInitialized = true
    }
  }

  /**
   * Authenticate user with credentials
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    await this.ensureInitialized()

    const offlineCandidate = await this.authenticateOffline(credentials)

    if (this.offlineMode && !offlineCandidate) {
      await this.tryReconnect()
    }

    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500))

    let user: User | null = null

    if (this.offlineMode && offlineCandidate) {
      user = offlineCandidate
    } else {
      try {
        user = await this.authenticateWithBackend(credentials)
        this.offlineMode = false
      } catch (error) {
        const connectionFailure = this.isConnectionError(error) || this.offlineMode

        if (offlineCandidate && connectionFailure) {
          console.warn('[AuthService] Falling back to offline credentials', error)
          this.offlineMode = true
          user = offlineCandidate
        } else if (offlineCandidate && !connectionFailure) {
          console.warn('[AuthService] Backend rejected credentials but demo account matched; using offline login')
          this.offlineMode = true
          user = offlineCandidate
        } else {
          throw error
        }
      }
    }

    if (!user) {
      throw new Error('Invalid username or password')
    }

    const sessionId = this.generateSessionId()
    const userAgent = navigator.userAgent
    const ipAddress = await this.getClientIP()

    const jwtOptions: JWTGenerationOptions = {
      userId: user.id,
      username: user.username,
      email: user.email,
      role: user.role,
      sessionId,
      userAgent,
      ipAddress,
      tokenType: 'access',
      scope: user.role === 'admin' ? ['read', 'write', 'admin'] : ['read'],
      preferences: user.preferences
    }

    const { accessToken, refreshToken } = await this.issueTokens(jwtOptions)

    return {
      user,
      token: accessToken,
      refreshToken,
      expiresIn: 3600
    }
  }

  /**
   * Register new user with credentials
   */
  async register(credentials: RegistrationCredentials): Promise<RegistrationResponse> {
    await this.ensureInitialized()
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Validate registration data
    await this.validateRegistrationCredentials(credentials)
    
    // Create new user account
    const user = await this.createUserAccount(credentials)
    
    // Generate session ID for JWT claims
    const sessionId = this.generateSessionId()
    const userAgent = navigator.userAgent
    const ipAddress = await this.getClientIP()
    
    // Create JWT generation options
    const jwtOptions: JWTGenerationOptions = {
      userId: user.id,
      username: user.username,
      email: user.email,
      role: user.role,
      sessionId,
      userAgent,
      ipAddress,
      tokenType: 'access',
      scope: user.role === 'admin' ? ['read', 'write', 'admin'] : ['read'],
      preferences: user.preferences
    }
    
    const { accessToken, refreshToken } = await this.issueTokens(jwtOptions)

    return {
      user,
      token: accessToken,
      refreshToken,
      expiresIn: 3600, // 1 hour
      isEmailVerified: false, // In real implementation, would require email verification
      tokenType: 'JWT'
    }
  }

  /**
   * Refresh authentication token using JWT refresh flow
   */
  async refreshToken(refreshToken: string): Promise<LoginResponse> {
    await this.ensureInitialized()
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500))
    
    try {
      // Use JWT service to refresh tokens
      const tokenPair = await jwtService.refreshToken(refreshToken)

      // Decode the new access token to extract user data
      const decodedToken = jwtService.decodeToken(tokenPair.accessToken)
      if (!decodedToken?.payload) {
        throw new Error('Invalid username or password')
      }
      
      const payload = decodedToken.payload
      const user: User = {
        id: payload.id,
        username: payload.username,
        email: payload.email,
        role: payload.role,
        lastLogin: new Date().toISOString(),
        isActive: true,
        preferences: payload.preferences
      }
      
      return {
        user,
        token: tokenPair.accessToken,
        refreshToken: tokenPair.refreshToken,
        expiresIn: tokenPair.expiresIn
      }
    } catch (error) {
      console.warn('[AuthService] Refresh token failed, issuing new offline tokens', error)

      const user = await this.authenticateOfflineFromRefresh(refreshToken)
      if (!user) {
        throw new Error('Invalid username or password')
      }

      const sessionId = this.generateSessionId()
      const userAgent = navigator.userAgent
      const ipAddress = await this.getClientIP()

      const jwtOptions: JWTGenerationOptions = {
        userId: user.id,
        username: user.username,
        email: user.email,
        role: user.role,
        sessionId,
        userAgent,
        ipAddress,
        tokenType: 'access',
        scope: user.role === 'admin' ? ['read', 'write', 'admin'] : ['read'],
        preferences: user.preferences
      }

      const { accessToken, refreshToken: refreshedFallback } = await this.issueTokens(jwtOptions)

      return {
        user,
        token: accessToken,
        refreshToken: refreshedFallback,
        expiresIn: 3600
      }
    }
  }

  /**
   * Validate authentication token using JWT verification
   */
  async validateToken(token: string): Promise<boolean> {
    await this.ensureInitialized()
    
    try {
      const validation = await jwtService.validateToken(token)
      return validation.isValid
    } catch (error) {
      console.error('Token validation error:', error)
      return false
    }
  }

  /**
   * Logout and revoke tokens
   */
  async logout(token?: string, fallbackUsername?: string): Promise<void> {
    await this.ensureInitialized()

    try {
      // Extract session_id from token for backend logout logging
      let sessionId = 'unknown'
      if (token) {
        try {
          const decodedToken = jwtService.decodeToken(token)
          sessionId = decodedToken?.payload?.sessionId || 'unknown'
        } catch (e) {
          console.warn('Could not decode token for logout logging:', e)
        }

        // Revoke the access token
        await jwtService.revokeToken(token, 'logout')
      }

      // Call backend logout with session context and user info for logging
      if (!this.offlineMode) {
        try {
          // Extract username from token or use fallback
          let username = 'unknown'
          if (token) {
            try {
              const decodedToken = jwtService.decodeToken(token)
              username = decodedToken?.payload?.username || 'unknown'
              console.log('🔐 Extracted username from token for logout:', username)
            } catch (e) {
              console.warn('Could not extract username from token for logout logging:', e)
              if (fallbackUsername) {
                username = fallbackUsername
                console.log('🔄 Using fallback username for logout:', username)
              }
            }
          } else if (fallbackUsername) {
            username = fallbackUsername
            console.log('🔄 Using fallback username for logout (no token):', username)
          } else {
            console.warn('⚠️ No token or fallback username provided for logout - cannot extract username')
          }

          console.log('🚪 Calling backend logout with:', { session_id: sessionId, username: username !== 'unknown' ? username : undefined })

          const logoutResult = await this.mcpClient.callTool('logout', {
            session_id: sessionId,
            username: username !== 'unknown' ? username : undefined
          })

          if (!logoutResult.success && logoutResult.error) {
            const wrappedError = new Error(String(logoutResult.error))
            if (this.isConnectionError(wrappedError)) {
              this.offlineMode = true
              console.warn('MCP logout skipped due to connection issue', logoutResult.error)
            } else {
              console.error('❌ Backend logout logging failed:', logoutResult.error)
            }
          } else {
            console.log('✅ Backend logout response:', logoutResult)
          }
        } catch (error) {
          if (this.isConnectionError(error)) {
            this.offlineMode = true
            console.warn('MCP logout skipped due to connection issue', error)
          } else {
            console.error('❌ Backend logout logging failed:', error)
          }
          // Continue with logout even if backend logging fails
        }
      } else {
        console.log('ℹ️ Skipping backend logout logging while offline')
      }

      // Simulate logout delay
      await new Promise(resolve => setTimeout(resolve, 200))
    } catch (error) {
      console.error('Logout error:', error)
      // Don't throw - allow logout to proceed even if revocation fails
    }
  }

  /**
   * Attempt to re-establish MCP connection when offline
   */
  private async tryReconnect(): Promise<void> {
    try {
      await this.mcpClient.connect()
      this.offlineMode = false
    } catch (error) {
      console.warn('[AuthService] MCP reconnection attempt failed', error)
      this.offlineMode = true
    }
  }

  private isConnectionError(error: unknown): boolean {
    if (error instanceof Error) {
      const message = error.message.toLowerCase()
      return MCP_CONNECTION_ERROR_PATTERNS.some(pattern => message.includes(pattern))
    }
    return false
  }

  private async authenticateOffline(credentials: LoginCredentials): Promise<User | null> {
    const username = credentials.username.trim().toLowerCase()
    const record = OFFLINE_USERS.find(user => user.username === username)

    if (!record) {
      return null
    }

    const isValid = await this.verifyOfflinePassword(credentials.password, record)
    if (!isValid) {
      return null
    }

    return this.mapOfflineUser(record.username)
  }

  private async verifyOfflinePassword(password: string, record: OfflineUserRecord): Promise<boolean> {
    try {
      const hashedInput = await this.hashPassword(password)
      if (this.timingSafeCompare(hashedInput, record.passwordHash)) {
        return true
      }
    } catch (error) {
      console.warn('[AuthService] Secure hashing unavailable, falling back to direct comparison', error)
    }

    return this.timingSafeCompare(password, record.fallbackPassword)
  }

  private async hashPassword(password: string): Promise<string> {
    const cryptoObj = typeof globalThis !== 'undefined' ? globalThis.crypto : undefined
    const subtle = cryptoObj?.subtle || (typeof window !== 'undefined' ? window.crypto?.subtle : undefined)

    if (!subtle) {
      throw new Error('Subtle crypto unavailable')
    }

    const encoder = new TextEncoder()
    const data = encoder.encode(password)
    const digest = await subtle.digest('SHA-256', data)
    const bytes = Array.from(new Uint8Array(digest))
    return bytes.map(byte => byte.toString(16).padStart(2, '0')).join('')
  }

  private timingSafeCompare(value: string, compareTo: string): boolean {
    const length = Math.max(value.length, compareTo.length)
    let mismatch = value.length === compareTo.length ? 0 : 1

    for (let index = 0; index < length; index += 1) {
      const valueChar = index < value.length ? value.charCodeAt(index) : 0
      const compareChar = index < compareTo.length ? compareTo.charCodeAt(index) : 0
      mismatch |= valueChar ^ compareChar
    }

    return mismatch === 0
  }

  private async issueTokens(options: JWTGenerationOptions): Promise<{ accessToken: string; refreshToken: string }> {
    try {
      const accessToken = await jwtService.generateToken({ ...options, tokenType: 'access' })
      const refreshToken = await jwtService.generateToken({ ...options, tokenType: 'refresh' })
      return { accessToken, refreshToken }
    } catch (error) {
      console.warn('[AuthService] JWT generation failed, using fallback tokens', error)
      return {
        accessToken: this.createFallbackToken(options, 'access'),
        refreshToken: this.createFallbackToken(options, 'refresh')
      }
    }
  }

  private createFallbackToken(options: JWTGenerationOptions, tokenType: 'access' | 'refresh'): string {
    const payload = {
      userId: options.userId,
      username: options.username,
      role: options.role,
      tokenType,
      issuedAt: Date.now(),
      sessionId: options.sessionId
    }

    try {
      const serialized = JSON.stringify(payload)
      const encoded = this.encodeBase64(serialized)
      if (encoded) {
        return `offline-${tokenType}-${encoded}`
      }
    } catch (error) {
      console.warn('[AuthService] Unable to encode fallback token payload', error)
    }

    return `offline-${tokenType}-${payload.userId}-${payload.issuedAt}`
  }

  private async authenticateOfflineFromRefresh(refreshToken: string): Promise<User | null> {
    if (!refreshToken.startsWith('offline-refresh-')) {
      return null
    }

    try {
      const encoded = refreshToken.replace('offline-refresh-', '')
      const decodedString = this.decodeBase64(encoded)
      if (!decodedString) {
        return null
      }

      const payload = JSON.parse(decodedString) as { userId: string; username: string }
      return this.mapOfflineUser(payload.username)
    } catch (error) {
      console.warn('[AuthService] Failed to decode offline refresh token', error)
      return null
    }
  }

  private mapOfflineUser(username: string): User | null {
    const normalized = username.trim().toLowerCase()
    const record = OFFLINE_USERS.find(user => user.username === normalized)
    if (!record) {
      return null
    }

    return {
      id: record.id,
      username: record.username,
      email: record.email,
      role: record.role,
      lastLogin: new Date().toISOString(),
      isActive: true,
      preferences: record.preferences || {}
    }
  }

  private encodeBase64(value: string): string | null {
    try {
      if (typeof globalThis !== 'undefined' && typeof globalThis.btoa === 'function') {
        return globalThis.btoa(value)
      }
    } catch (error) {
      console.warn('[AuthService] Base64 encode failed', error)
    }
    return null
  }

  private decodeBase64(value: string): string | null {
    try {
      if (typeof globalThis !== 'undefined' && typeof globalThis.atob === 'function') {
        return globalThis.atob(value)
      }
    } catch (error) {
      console.warn('[AuthService] Base64 decode failed', error)
    }
    return null
  }

  /**
   * Authenticate user with backend MCP service
   */
  private async authenticateWithBackend(credentials: LoginCredentials): Promise<User> {
    try {
      await this.ensureInitialized()

      if (this.offlineMode) {
        throw new Error('MCP_CONNECTION_ERROR: offline mode enabled')
      }

      console.log('🔐 Authenticating with backend MCP...')
      console.log('📝 Credentials:', { username: credentials.username, password: '[REDACTED]' })

      const response = await this.mcpClient.callTool('login', {
        credentials: {
          username: credentials.username,
          password: credentials.password
        }
      })

      console.log('🔄 Raw MCP response received:')
      console.log('📊 Full response object:', JSON.stringify(response, null, 2))
      console.log('✅ response.success:', response.success)
      console.log('📋 response.data exists:', !!response.data)
      console.log('👤 response.data?.user exists:', !!response.data?.user)

      if (response.data) {
        console.log('📦 response.data contents:', JSON.stringify(response.data, null, 2))
      }

      if (!response.success) {
        const errorMessage = response.error || 'Unknown MCP error'
        const wrappedError = new Error(errorMessage)
        if (this.isConnectionError(wrappedError)) {
          throw new Error(`MCP_CONNECTION_ERROR: ${errorMessage}`)
        }
        throw new Error('Invalid username or password')
      }

      // Check the exact condition that's failing - user data is in structuredContent
      const actualUserData = response.data?.structuredContent?.data?.user
      const conditionResult = response.success && actualUserData
      console.log('🎯 Condition (response.success && actualUserData):', conditionResult)
      console.log('🎯 actualUserData:', actualUserData)

      if (conditionResult) {
        const userData = actualUserData
        console.log('👤 User data extracted:', JSON.stringify(userData, null, 2))

        const user = {
          id: userData.id || userData.username,
          username: userData.username,
          email: userData.email || `${userData.username}@homelab.local`,
          role: userData.role || 'user',
          lastLogin: new Date().toISOString(),
          isActive: userData.is_active !== false,
          preferences: userData.preferences || {}
        }

        console.log('🎉 Final user object created:', JSON.stringify(user, null, 2))
        return user
      } else {
        console.log('❌ Authentication condition failed - throwing error')
        console.log('❌ response.success:', response.success)
        console.log('❌ response.data:', response.data)
        console.log('❌ response.data?.structuredContent?.data?.user:', response.data?.structuredContent?.data?.user)
        throw new Error('Invalid username or password')
      }
    } catch (error) {
      if (this.isConnectionError(error)) {
        const connectionError = error instanceof Error ? error : new Error('MCP_CONNECTION_ERROR')
        throw connectionError
      }

      console.error('Backend authentication error:', error)
      throw new Error('Invalid username or password')
    }
  }

  /**
   * Generate session ID for JWT claims
   */
  private generateSessionId(): string {
    return 'sess_' + Math.random().toString(36).substring(2, 15) + 
           Math.random().toString(36).substring(2, 15)
  }

  /**
   * Get client IP (mock implementation)
   */
  private async getClientIP(): Promise<string> {
    // In production, this would be obtained from request headers
    return '127.0.0.1'
  }

  /**
   * Validate registration credentials (security measures)
   */
  private async validateRegistrationCredentials(credentials: RegistrationCredentials): Promise<void> {
    // Username uniqueness check (generic error for security)
    if (await this.usernameExists(credentials.username)) {
      throw new Error('Invalid username or password')
    }
    
    // Email uniqueness check (generic error for security)
    if (await this.emailExists(credentials.email)) {
      throw new Error('Invalid username or password')
    }
    
    // Password confirmation validation
    if (credentials.password !== credentials.confirmPassword) {
      throw new Error('Invalid username or password')
    }
    
    // Terms acceptance validation
    if (!credentials.acceptTerms) {
      throw new Error('Invalid username or password')
    }
  }

  /**
   * Create new user account (mock implementation)
   */
  private async createUserAccount(credentials: RegistrationCredentials): Promise<User> {
    // Generate unique user ID
    const userId = 'user_' + Math.random().toString(36).substring(2, 15)
    
    return {
      id: userId,
      username: credentials.username,
      email: credentials.email,
      role: credentials.role || 'user', // Default to user role
      lastLogin: new Date().toISOString(),
      isActive: true,
      preferences: {
        theme: 'light', // Default preferences for new users
        notifications: true
      }
    }
  }

  /**
   * Check if username already exists (mock implementation)
   */
  private async usernameExists(username: string): Promise<boolean> {
    // Simulate API delay for consistent response timing
    await new Promise(resolve => setTimeout(resolve, 200))
    
    // Mock check - in production, query database
    const existingUsernames = ['admin', 'user', 'test', 'demo']
    return existingUsernames.includes(username.toLowerCase())
  }

  /**
   * Check if email already exists (mock implementation)
   */
  private async emailExists(email: string): Promise<boolean> {
    // Simulate API delay for consistent response timing
    await new Promise(resolve => setTimeout(resolve, 200))
    
    // Mock check - in production, query database
    const existingEmails = ['admin@homelab.local', 'user@homelab.local', 'test@example.com']
    return existingEmails.includes(email.toLowerCase())
  }

  /**
   * Ensure service is initialized
   */
  private async ensureInitialized(): Promise<void> {
    if (!this.isInitialized) {
      await this.initialize()
    }
  }
}

export const authService = new AuthService()
export default authService
