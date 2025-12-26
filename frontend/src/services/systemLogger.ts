/**
 * System Logger Service
 * 
 * Centralized logging system for application events that can be viewed
 * in the system logs interface. Stores logs in memory and localStorage
 * for persistence across sessions.
 */

export interface SystemLogEntry {
  id: string
  timestamp: Date
  level: 'info' | 'warn' | 'error'
  category: string
  message: string
  data?: any
}

class SystemLogger {
  private logs: SystemLogEntry[] = []
  private maxLogs = 1000
  private storageKey = 'homelab-system-logs'

  constructor() {
    this.loadLogsFromStorage()
  }

  private loadLogsFromStorage() {
    try {
      const stored = localStorage.getItem(this.storageKey)
      if (stored) {
        const parsedLogs = JSON.parse(stored)
        this.logs = parsedLogs.map((log: any) => ({
          ...log,
          timestamp: new Date(log.timestamp)
        }))
      }
    } catch (error) {
      console.warn('Failed to load system logs from localStorage:', error)
    }
  }

  private saveLogsToStorage() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.logs))
    } catch (error) {
      console.warn('Failed to save system logs to localStorage:', error)
    }
  }

  private addLog(level: SystemLogEntry['level'], category: string, message: string, data?: any) {
    const entry: SystemLogEntry = {
      id: `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      level,
      category,
      message,
      data
    }

    this.logs.unshift(entry)

    // Keep only the most recent logs
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(0, this.maxLogs)
    }

    this.saveLogsToStorage()

    // Also log to console for debugging
    const consoleMessage = `[${category}] ${message}`
    switch (level) {
      case 'error':
        console.error(consoleMessage, data || '')
        break
      case 'warn':
        console.warn(consoleMessage, data || '')
        break
      default:
        console.info(consoleMessage, data || '')
    }
  }

  info(category: string, message: string, data?: any) {
    this.addLog('info', category, message, data)
  }

  warn(category: string, message: string, data?: any) {
    this.addLog('warn', category, message, data)
  }

  error(category: string, message: string, data?: any) {
    this.addLog('error', category, message, data)
  }

  getLogs(): SystemLogEntry[] {
    return [...this.logs]
  }

  getLogsByCategory(category: string): SystemLogEntry[] {
    return this.logs.filter(log => log.category === category)
  }

  getLogsByLevel(level: SystemLogEntry['level']): SystemLogEntry[] {
    return this.logs.filter(log => log.level === level)
  }

  clearLogs() {
    this.logs = []
    this.saveLogsToStorage()
  }

  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2)
  }
}

// Export singleton instance
export const systemLogger = new SystemLogger()

// Convenience functions for common categories
export const mcpLogger = {
  info: (message: string, data?: any) => systemLogger.info('MCP', message, data),
  warn: (message: string, data?: any) => systemLogger.warn('MCP', message, data),
  error: (message: string, data?: any) => systemLogger.error('MCP', message, data)
}

export const settingsLogger = {
  info: (message: string, data?: any) => systemLogger.info('Settings', message, data),
  warn: (message: string, data?: any) => systemLogger.warn('Settings', message, data),
  error: (message: string, data?: any) => systemLogger.error('Settings', message, data)
}

export const applicationLogger = {
  info: (message: string, data?: any) => systemLogger.info('application', message, data),
  warn: (message: string, data?: any) => systemLogger.warn('application', message, data),
  error: (message: string, data?: any) => systemLogger.error('application', message, data)
}

export const securityLogger = {
  info: (message: string, data?: any) => systemLogger.info('Security', message, data),
  warn: (message: string, data?: any) => systemLogger.warn('Security', message, data),
  error: (message: string, data?: any) => systemLogger.error('Security', message, data)
}
