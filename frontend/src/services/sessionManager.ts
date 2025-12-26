/**
 * Session Manager Service
 * 
 * Enhanced session management with multi-session support, real-time tracking,
 * and comprehensive session metadata collection for the Security Settings table.
 */

import { sessionService } from './auth/sessionService'
import { authApi } from './api/authApi'
import { 
  detectIPAddress, 
  getLocationInfo, 
  parseDeviceInfo, 
  formatDeviceString,
  createActivityTracker,
  startActivityTracking,
  SessionActivity,
  DeviceInfo,
  LocationInfo
} from '@/utils/sessionMetadata'

export interface SessionListEntry {
  id: string
  sessionId: string
  userId: string
  status: 'active' | 'idle' | 'expired'
  started: Date
  lastActivity: Date
  location: string
  ip: string
  deviceInfo: DeviceInfo
  locationInfo: LocationInfo
  activity: SessionActivity
  isCurrentSession: boolean
  duration: number
}

export interface SessionManagerConfig {
  refreshInterval: number // ms
  idleTimeout: number // ms
  maxSessions: number
  trackActivity: boolean
}

const DEFAULT_CONFIG: SessionManagerConfig = {
  refreshInterval: 30000, // 30 seconds
  idleTimeout: 300000, // 5 minutes
  maxSessions: 10,
  trackActivity: true
}

class SessionManager {
  private config: SessionManagerConfig
  private sessions: Map<string, SessionListEntry> = new Map()
  private currentSessionId: string | null = null
  private refreshTimer: NodeJS.Timeout | null = null
  private activityCleanup: (() => void) | null = null
  private listeners: Set<(sessions: SessionListEntry[]) => void> = new Set()

  constructor(config: Partial<SessionManagerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config }
  }

  /**
   * Initialize session manager and load existing sessions
   */
  async initialize(): Promise<void> {
    try {
      // Load current session from sessionService
      await this.loadCurrentSession()
      
      // Load additional sessions from storage/API
      await this.loadStoredSessions()
      
      // Start real-time tracking
      this.startRealTimeTracking()
      
      console.log('[SessionManager] Initialized with', this.sessions.size, 'sessions')
    } catch (error) {
      console.error('[SessionManager] Initialization failed:', error)
      throw error
    }
  }

  /**
   * Get all user sessions as list
   */
  getUserSessions(): SessionListEntry[] {
    return Array.from(this.sessions.values())
      .sort((a, b) => {
        // Current session first
        if (a.isCurrentSession) return -1
        if (b.isCurrentSession) return 1
        
        // Then by last activity (most recent first)
        return b.lastActivity.getTime() - a.lastActivity.getTime()
      })
  }

  /**
   * Get specific session by ID
   */
  getSession(sessionId: string): SessionListEntry | null {
    return this.sessions.get(sessionId) || null
  }

  /**
   * Get current active session
   */
  getCurrentSession(): SessionListEntry | null {
    return this.currentSessionId ? this.sessions.get(this.currentSessionId) || null : null
  }

  /**
   * Create new session entry
   */
  async createSession(userId: string): Promise<SessionListEntry> {
    try {
      // Get session metadata
      const ipAddress = await detectIPAddress()
      const deviceInfo = parseDeviceInfo()
      const locationInfo = await getLocationInfo(ipAddress)
      
      // Generate session ID
      const sessionId = `sess_${Date.now()}_${Math.random().toString(36).substr(2, 8)}`
      
      const now = new Date()
      const sessionEntry: SessionListEntry = {
        id: sessionId.slice(-12), // Display ID (last 12 chars)
        sessionId,
        userId,
        status: 'active',
        started: now,
        lastActivity: now,
        location: formatDeviceString(deviceInfo),
        ip: ipAddress,
        deviceInfo,
        locationInfo,
        activity: createActivityTracker(),
        isCurrentSession: true,
        duration: 0
      }

      // Set as current session
      if (this.currentSessionId && this.sessions.has(this.currentSessionId)) {
        const oldCurrent = this.sessions.get(this.currentSessionId)!
        oldCurrent.isCurrentSession = false
      }
      
      this.currentSessionId = sessionId
      this.sessions.set(sessionId, sessionEntry)
      
      // Start activity tracking for current session
      this.startActivityTracking(sessionEntry)
      
      // Persist session
      await this.persistSession(sessionEntry)
      
      // Notify listeners
      this.notifyListeners()
      
      console.log('[SessionManager] Created session:', sessionId)
      return sessionEntry
    } catch (error) {
      console.error('[SessionManager] Failed to create session:', error)
      throw error
    }
  }

  /**
   * Terminate specific session
   */
  async terminateSession(sessionId: string): Promise<void> {
    try {
      const session = this.sessions.get(sessionId)
      
      if (!session) {
        console.warn('[SessionManager] Session not found:', sessionId)
        return
      }

      if (session.isCurrentSession) {
        // Terminating current session - full logout
        await sessionService.destroySession()
        await authApi.logout()
        
        // Clear all session data
        this.sessions.clear()
        this.currentSessionId = null
        this.stopRealTimeTracking()
      } else {
        // Terminate remote session
        await authApi.terminateSession(sessionId)
        this.sessions.delete(sessionId)
        
        // Remove from persistent storage
        await this.removePersistedSession(sessionId)
      }
      
      console.log('[SessionManager] Terminated session:', sessionId)
      this.notifyListeners()
    } catch (error) {
      console.error('[SessionManager] Failed to terminate session:', error)
      throw error
    }
  }

  /**
   * Refresh session data from server
   */
  async refreshSessions(): Promise<void> {
    try {
      // Validate current session
      const currentSession = sessionService.getCurrentSession()
      
      if (currentSession && this.currentSessionId) {
        const sessionEntry = this.sessions.get(this.currentSessionId)
        
        if (sessionEntry) {
          // Update current session metadata
          sessionEntry.lastActivity = new Date(currentSession.lastActivity)
          sessionEntry.duration = Date.now() - sessionEntry.started.getTime()
          
          // Update session status based on activity
          const timeSinceActivity = Date.now() - sessionEntry.lastActivity.getTime()
          
          if (timeSinceActivity > this.config.idleTimeout) {
            sessionEntry.status = 'idle'
          } else {
            sessionEntry.status = 'active'
          }
          
          // Persist updated session
          await this.persistSession(sessionEntry)
        }
      }
      
      // In production, fetch additional sessions from backend API
      // const remoteSessionsResponse = await authApi.listUserSessions(userId)
      // this.syncRemoteSessions(remoteSessionsResponse.sessions)
      
      this.notifyListeners()
    } catch (error) {
      console.error('[SessionManager] Failed to refresh sessions:', error)
    }
  }

  /**
   * Add session update listener
   */
  addListener(callback: (sessions: SessionListEntry[]) => void): () => void {
    this.listeners.add(callback)
    
    // Return unsubscribe function
    return () => {
      this.listeners.delete(callback)
    }
  }

  /**
   * Clean up resources
   */
  destroy(): void {
    this.stopRealTimeTracking()
    this.sessions.clear()
    this.listeners.clear()
    this.currentSessionId = null
    
    console.log('[SessionManager] Destroyed')
  }

  /**
   * Load current session from sessionService
   */
  private async loadCurrentSession(): Promise<void> {
    const currentSession = sessionService.getCurrentSession()
    
    if (!currentSession) {
      console.log('[SessionManager] No current session found')
      return
    }

    try {
      const deviceInfo = parseDeviceInfo()
      const locationInfo = await getLocationInfo(currentSession.ipAddress)
      
      const sessionEntry: SessionListEntry = {
        id: currentSession.sessionId.slice(-12),
        sessionId: currentSession.sessionId,
        userId: currentSession.userId,
        status: 'active',
        started: new Date(currentSession.startTime),
        lastActivity: new Date(currentSession.lastActivity),
        location: `Current Session - ${formatDeviceString(deviceInfo)}`,
        ip: currentSession.ipAddress,
        deviceInfo,
        locationInfo,
        activity: createActivityTracker(),
        isCurrentSession: true,
        duration: Date.now() - new Date(currentSession.startTime).getTime()
      }

      this.currentSessionId = currentSession.sessionId
      this.sessions.set(currentSession.sessionId, sessionEntry)
      
      // Start activity tracking
      this.startActivityTracking(sessionEntry)
      
      console.log('[SessionManager] Loaded current session:', currentSession.sessionId)
    } catch (error) {
      console.error('[SessionManager] Failed to load current session:', error)
    }
  }

  /**
   * Load additional sessions from local storage
   */
  private async loadStoredSessions(): Promise<void> {
    try {
      const storedSessionsJson = localStorage.getItem('sessionManager_sessions')
      
      if (storedSessionsJson) {
        const storedSessions = JSON.parse(storedSessionsJson) as SessionListEntry[]
        const now = new Date()
        
        for (const session of storedSessions) {
          // Skip if it's the current session (already loaded)
          if (session.isCurrentSession) continue
          
          // Check if session is expired
          const timeSinceActivity = now.getTime() - new Date(session.lastActivity).getTime()
          
          if (timeSinceActivity > 24 * 60 * 60 * 1000) { // 24 hours
            session.status = 'expired'
          }
          
          // Restore Date objects
          session.started = new Date(session.started)
          session.lastActivity = new Date(session.lastActivity)
          session.duration = now.getTime() - session.started.getTime()
          
          this.sessions.set(session.sessionId, session)
        }
        
        console.log('[SessionManager] Loaded', storedSessions.length, 'stored sessions')
      } else {
        // No stored sessions, create some demo sessions for testing
        await this.createDemoSessions()
      }
    } catch (error) {
      console.error('[SessionManager] Failed to load stored sessions:', error)
      // Fallback to demo sessions
      await this.createDemoSessions()
    }
  }

  /**
   * Create demo sessions for testing
   */
  private async createDemoSessions(): Promise<void> {
    const now = new Date()
    const demoSessions: SessionListEntry[] = [
      {
        id: '****8b9c',
        sessionId: 'sess_1703856000000_8b9c1234',
        userId: 'demo-user',
        status: 'idle',
        started: new Date(now.getTime() - 2 * 60 * 60 * 1000), // 2 hours ago
        lastActivity: new Date(now.getTime() - 15 * 60 * 1000), // 15 minutes ago
        location: 'Chrome 120 on macOS 14.1',
        ip: '192.168.1.100',
        deviceInfo: {
          browser: 'Chrome',
          browserVersion: '120.0',
          os: 'macOS',
          osVersion: '14.1',
          deviceType: 'desktop',
          isMobile: false
        },
        locationInfo: {
          country: 'US',
          region: 'CA',
          city: 'San Francisco',
          timezone: 'America/Los_Angeles'
        },
        activity: {
          pageViews: 25,
          keystrokes: 450,
          mouseClicks: 120,
          idleTime: 15 * 60 * 1000,
          lastActiveTab: 'Dashboard'
        },
        isCurrentSession: false,
        duration: 2 * 60 * 60 * 1000
      },
      {
        id: '****3d2f',
        sessionId: 'sess_1703769600000_3d2f5678',
        userId: 'demo-user',
        status: 'expired',
        started: new Date(now.getTime() - 24 * 60 * 60 * 1000), // 24 hours ago
        lastActivity: new Date(now.getTime() - 8 * 60 * 60 * 1000), // 8 hours ago
        location: 'Firefox 121 on Windows 11',
        ip: '192.168.1.150',
        deviceInfo: {
          browser: 'Firefox',
          browserVersion: '121.0',
          os: 'Windows',
          osVersion: '11',
          deviceType: 'desktop',
          isMobile: false
        },
        locationInfo: {
          country: 'US',
          region: 'NY',
          city: 'New York',
          timezone: 'America/New_York'
        },
        activity: {
          pageViews: 45,
          keystrokes: 890,
          mouseClicks: 220,
          idleTime: 8 * 60 * 60 * 1000,
          lastActiveTab: 'Settings'
        },
        isCurrentSession: false,
        duration: 16 * 60 * 60 * 1000
      },
      {
        id: '****9a7e',
        sessionId: 'sess_1703852400000_9a7e9012',
        userId: 'demo-user',
        status: 'active',
        started: new Date(now.getTime() - 45 * 60 * 1000), // 45 minutes ago
        lastActivity: new Date(now.getTime() - 2 * 60 * 1000), // 2 minutes ago
        location: 'Safari 17 on iPhone 15',
        ip: '10.0.1.50',
        deviceInfo: {
          browser: 'Safari',
          browserVersion: '17.0',
          os: 'iOS',
          osVersion: '17.2',
          deviceType: 'mobile',
          isMobile: true
        },
        locationInfo: {
          country: 'US',
          region: 'CA',
          city: 'Los Angeles',
          timezone: 'America/Los_Angeles'
        },
        activity: {
          pageViews: 12,
          keystrokes: 180,
          mouseClicks: 65,
          idleTime: 2 * 60 * 1000,
          lastActiveTab: 'Logs'
        },
        isCurrentSession: false,
        duration: 43 * 60 * 1000
      }
    ]

    // Add demo sessions to the map
    for (const session of demoSessions) {
      this.sessions.set(session.sessionId, session)
    }

    // Persist demo sessions
    await this.persistSession(demoSessions[0]) // This will save all sessions
    
    console.log('[SessionManager] Created', demoSessions.length, 'demo sessions')
  }

  /**
   * Start activity tracking for current session
   */
  private startActivityTracking(sessionEntry: SessionListEntry): void {
    if (!this.config.trackActivity) return
    
    // Clean up existing tracking
    if (this.activityCleanup) {
      this.activityCleanup()
    }
    
    this.activityCleanup = startActivityTracking(
      sessionEntry.activity,
      (updatedActivity) => {
        sessionEntry.activity = updatedActivity
        sessionEntry.lastActivity = new Date()
        
        // Update status based on activity
        sessionEntry.status = 'active'
        
        // Persist changes (debounced)
        this.debouncePeristSession(sessionEntry)
      }
    )
  }

  /**
   * Start real-time session tracking
   */
  private startRealTimeTracking(): void {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer)
    }
    
    this.refreshTimer = setInterval(() => {
      this.refreshSessions()
    }, this.config.refreshInterval)
  }

  /**
   * Stop real-time session tracking
   */
  private stopRealTimeTracking(): void {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer)
      this.refreshTimer = null
    }
    
    if (this.activityCleanup) {
      this.activityCleanup()
      this.activityCleanup = null
    }
  }

  /**
   * Persist session to storage
   */
  private async persistSession(_session: SessionListEntry): Promise<void> {
    try {
      const allSessions = Array.from(this.sessions.values())
      localStorage.setItem('sessionManager_sessions', JSON.stringify(allSessions))
    } catch (error) {
      console.error('[SessionManager] Failed to persist session:', error)
    }
  }

  /**
   * Remove session from persistent storage
   */
  private async removePersistedSession(_sessionId: string): Promise<void> {
    try {
      const allSessions = Array.from(this.sessions.values())
      localStorage.setItem('sessionManager_sessions', JSON.stringify(allSessions))
    } catch (error) {
      console.error('[SessionManager] Failed to remove persisted session:', error)
    }
  }

  /**
   * Debounced session persistence to avoid too frequent writes
   */
  private debouncePeristSession = this.debounce((session: SessionListEntry) => {
    this.persistSession(session)
  }, 5000)

  /**
   * Notify all listeners of session changes
   */
  private notifyListeners(): void {
    const sessions = this.getUserSessions()
    this.listeners.forEach(callback => {
      try {
        callback(sessions)
      } catch (error) {
        console.error('[SessionManager] Listener error:', error)
      }
    })
  }

  /**
   * Debounce utility function
   */
  private debounce<T extends unknown[]>(
    func: (...args: T) => void, 
    wait: number
  ): (...args: T) => void {
    let timeout: NodeJS.Timeout
    
    return (...args: T) => {
      clearTimeout(timeout)
      timeout = setTimeout(() => func(...args), wait)
    }
  }
}

export const sessionManager = new SessionManager()
export default sessionManager
