/**
 * Session Manager Service
 *
 * Enhanced session management with multi-session support, real-time tracking,
 * and comprehensive session metadata collection for the Security Settings table.
 */

import { sessionService } from './auth/sessionService';
import { authApi } from './api/authApi';
import { cryptoRandomString } from '@/utils/jwtUtils';
import { securityLogger } from '@/services/systemLogger';
import { createDemoSessions } from './fixtures/demoSessions';
import {
  detectIPAddress,
  getLocationInfo,
  parseDeviceInfo,
  formatDeviceString,
  createActivityTracker,
  startActivityTracking,
  SessionActivity,
  DeviceInfo,
  LocationInfo,
} from '@/utils/sessionMetadata';

export interface SessionListEntry {
  id: string;
  sessionId: string;
  userId: string;
  status: 'active' | 'idle' | 'expired';
  started: Date;
  lastActivity: Date;
  location: string;
  ip: string;
  deviceInfo: DeviceInfo;
  locationInfo: LocationInfo;
  activity: SessionActivity;
  isCurrentSession: boolean;
  duration: number;
}

export interface SessionManagerConfig {
  refreshInterval: number; // ms
  idleTimeout: number; // ms
  maxSessions: number;
  trackActivity: boolean;
}

const DEFAULT_CONFIG: SessionManagerConfig = {
  refreshInterval: 30000, // 30 seconds
  idleTimeout: 300000, // 5 minutes
  maxSessions: 10,
  trackActivity: true,
};

class SessionManager {
  private config: SessionManagerConfig;
  private sessions: Map<string, SessionListEntry> = new Map();
  private currentSessionId: string | null = null;
  private refreshTimer: NodeJS.Timeout | null = null;
  private activityCleanup: (() => void) | null = null;
  private listeners: Set<(sessions: SessionListEntry[]) => void> = new Set();

  constructor(config: Partial<SessionManagerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Initialize session manager and load existing sessions
   */
  async initialize(): Promise<void> {
    try {
      // Load current session from sessionService
      await this.loadCurrentSession();

      // Load additional sessions from storage/API
      await this.loadStoredSessions();

      // Start real-time tracking
      this.startRealTimeTracking();

      securityLogger.info('Initialized with ' + this.sessions.size + ' sessions');
    } catch (error) {
      securityLogger.error('Initialization failed', { error: String(error) });
      throw error;
    }
  }

  /**
   * Get all user sessions as list
   */
  getUserSessions(): SessionListEntry[] {
    return Array.from(this.sessions.values()).sort((a, b) => {
      // Current session first
      if (a.isCurrentSession) return -1;
      if (b.isCurrentSession) return 1;

      // Then by last activity (most recent first)
      return b.lastActivity.getTime() - a.lastActivity.getTime();
    });
  }

  /**
   * Get specific session by ID
   */
  getSession(sessionId: string): SessionListEntry | null {
    return this.sessions.get(sessionId) || null;
  }

  /**
   * Get current active session
   */
  getCurrentSession(): SessionListEntry | null {
    return this.currentSessionId ? this.sessions.get(this.currentSessionId) || null : null;
  }

  /**
   * Create new session entry
   */
  async createSession(userId: string): Promise<SessionListEntry> {
    try {
      // Get session metadata
      const ipAddress = await detectIPAddress();
      const deviceInfo = parseDeviceInfo();
      const locationInfo = await getLocationInfo(ipAddress);

      // Generate session ID
      const sessionId = `sess_${Date.now()}_${cryptoRandomString(6)}`;

      const now = new Date();
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
        duration: 0,
      };

      // Set as current session
      if (this.currentSessionId && this.sessions.has(this.currentSessionId)) {
        const oldCurrent = this.sessions.get(this.currentSessionId)!;
        oldCurrent.isCurrentSession = false;
      }

      this.currentSessionId = sessionId;
      this.sessions.set(sessionId, sessionEntry);

      // Start activity tracking for current session
      this.startActivityTracking(sessionEntry);

      // Persist session
      await this.persistSession(sessionEntry);

      // Notify listeners
      this.notifyListeners();

      securityLogger.info('Session created', { sessionId });
      return sessionEntry;
    } catch (error) {
      console.error('[SessionManager] Failed to create session:', error);
      throw error;
    }
  }

  /**
   * Terminate specific session
   */
  async terminateSession(sessionId: string): Promise<void> {
    try {
      const session = this.sessions.get(sessionId);

      if (!session) {
        console.warn('[SessionManager] Session not found:', sessionId);
        return;
      }

      if (session.isCurrentSession) {
        // Terminating current session - full logout
        await sessionService.destroySession();
        await authApi.logout();

        // Clear all session data
        this.sessions.clear();
        this.currentSessionId = null;
        this.stopRealTimeTracking();
      } else {
        // Terminate remote session
        await authApi.terminateSession(sessionId);
        this.sessions.delete(sessionId);

        // Remove from persistent storage
        await this.removePersistedSession(sessionId);
      }

      securityLogger.info('Session terminated', { sessionId });
      this.notifyListeners();
    } catch (error) {
      securityLogger.error('Failed to terminate session', { error: String(error) });
      throw error;
    }
  }

  /**
   * Refresh session data from server
   */
  async refreshSessions(): Promise<void> {
    try {
      // Validate current session
      const currentSession = sessionService.getCurrentSession();

      if (currentSession && this.currentSessionId) {
        const sessionEntry = this.sessions.get(this.currentSessionId);

        if (sessionEntry) {
          // Update current session metadata
          sessionEntry.lastActivity = new Date(currentSession.lastActivity);
          sessionEntry.duration = Date.now() - sessionEntry.started.getTime();

          // Update session status based on activity
          const timeSinceActivity = Date.now() - sessionEntry.lastActivity.getTime();

          if (timeSinceActivity > this.config.idleTimeout) {
            sessionEntry.status = 'idle';
          } else {
            sessionEntry.status = 'active';
          }

          // Persist updated session
          await this.persistSession(sessionEntry);
        }
      }

      // In production, fetch additional sessions from backend API
      // const remoteSessionsResponse = await authApi.listUserSessions(userId)
      // this.syncRemoteSessions(remoteSessionsResponse.sessions)

      this.notifyListeners();
    } catch (error) {
      console.error('[SessionManager] Failed to refresh sessions:', error);
    }
  }

  /**
   * Add session update listener
   */
  addListener(callback: (sessions: SessionListEntry[]) => void): () => void {
    this.listeners.add(callback);

    // Return unsubscribe function
    return () => {
      this.listeners.delete(callback);
    };
  }

  /**
   * Clean up resources
   */
  destroy(): void {
    this.stopRealTimeTracking();
    this.sessions.clear();
    this.listeners.clear();
    this.currentSessionId = null;

    securityLogger.info('Session manager destroyed');
  }

  /**
   * Load current session from sessionService
   */
  private async loadCurrentSession(): Promise<void> {
    const currentSession = sessionService.getCurrentSession();

    if (!currentSession) {
      securityLogger.info('No current session found');
      return;
    }

    try {
      const deviceInfo = parseDeviceInfo();
      const locationInfo = await getLocationInfo(currentSession.ipAddress);

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
        duration: Date.now() - new Date(currentSession.startTime).getTime(),
      };

      this.currentSessionId = currentSession.sessionId;
      this.sessions.set(currentSession.sessionId, sessionEntry);

      // Start activity tracking
      this.startActivityTracking(sessionEntry);

      securityLogger.info('Loaded current session');
    } catch (error) {
      securityLogger.error('Failed to load current session', { error: String(error) });
    }
  }

  /**
   * Load additional sessions from local storage
   */
  private async loadStoredSessions(): Promise<void> {
    try {
      const storedSessionsJson = localStorage.getItem('sessionManager_sessions');

      if (storedSessionsJson) {
        const storedSessions = JSON.parse(storedSessionsJson) as SessionListEntry[];
        const now = new Date();

        for (const session of storedSessions) {
          // Skip if it's the current session (already loaded)
          if (session.isCurrentSession) continue;

          // Check if session is expired
          const timeSinceActivity = now.getTime() - new Date(session.lastActivity).getTime();

          if (timeSinceActivity > 24 * 60 * 60 * 1000) {
            // 24 hours
            session.status = 'expired';
          }

          // Restore Date objects
          session.started = new Date(session.started);
          session.lastActivity = new Date(session.lastActivity);
          session.duration = now.getTime() - session.started.getTime();

          this.sessions.set(session.sessionId, session);
        }

        securityLogger.info('Loaded ' + storedSessions.length + ' stored sessions');
      } else {
        // No stored sessions, create some demo sessions for testing
        await this.populateDemoSessions();
      }
    } catch (error) {
      securityLogger.error('Failed to load stored sessions', { error: String(error) });
      // Fallback to demo sessions
      await this.populateDemoSessions();
    }
  }

  /**
   * Create demo sessions for testing
   */
  private async populateDemoSessions(): Promise<void> {
    const demoSessions = createDemoSessions();

    for (const session of demoSessions) {
      this.sessions.set(session.sessionId, session);
    }

    await this.persistSession(demoSessions[0]);
    securityLogger.info('Created ' + demoSessions.length + ' demo sessions');
  }

  /**
   * Start activity tracking for current session
   */
  private startActivityTracking(sessionEntry: SessionListEntry): void {
    if (!this.config.trackActivity) return;

    // Clean up existing tracking
    if (this.activityCleanup) {
      this.activityCleanup();
    }

    this.activityCleanup = startActivityTracking(sessionEntry.activity, (updatedActivity) => {
      sessionEntry.activity = updatedActivity;
      sessionEntry.lastActivity = new Date();

      // Update status based on activity
      sessionEntry.status = 'active';

      // Persist changes (debounced)
      this.debouncePeristSession(sessionEntry);
    });
  }

  /**
   * Start real-time session tracking
   */
  private startRealTimeTracking(): void {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }

    this.refreshTimer = setInterval(() => {
      this.refreshSessions();
    }, this.config.refreshInterval);
  }

  /**
   * Stop real-time session tracking
   */
  private stopRealTimeTracking(): void {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }

    if (this.activityCleanup) {
      this.activityCleanup();
      this.activityCleanup = null;
    }
  }

  /**
   * Persist session to storage
   */
  private async persistSession(_session: SessionListEntry): Promise<void> {
    try {
      const allSessions = Array.from(this.sessions.values());
      localStorage.setItem('sessionManager_sessions', JSON.stringify(allSessions));
    } catch (error) {
      console.error('[SessionManager] Failed to persist session:', error);
    }
  }

  /**
   * Remove session from persistent storage
   */
  private async removePersistedSession(_sessionId: string): Promise<void> {
    try {
      const allSessions = Array.from(this.sessions.values());
      localStorage.setItem('sessionManager_sessions', JSON.stringify(allSessions));
    } catch (error) {
      console.error('[SessionManager] Failed to remove persisted session:', error);
    }
  }

  /**
   * Debounced session persistence to avoid too frequent writes
   */
  private debouncePeristSession = this.debounce((session: SessionListEntry) => {
    this.persistSession(session);
  }, 5000);

  /**
   * Notify all listeners of session changes
   */
  private notifyListeners(): void {
    const sessions = this.getUserSessions();
    this.listeners.forEach((callback) => {
      try {
        callback(sessions);
      } catch (error) {
        console.error('[SessionManager] Listener error:', error);
      }
    });
  }

  /**
   * Debounce utility function
   */
  private debounce<T extends unknown[]>(
    func: (...args: T) => void,
    wait: number
  ): (...args: T) => void {
    let timeout: NodeJS.Timeout;

    return (...args: T) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func(...args), wait);
    };
  }
}

export const sessionManager = new SessionManager();
export default sessionManager;
