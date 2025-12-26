/**
 * Security Settings Component
 * 
 * Session management and security configuration.
 */

import { SettingRow, SessionTable } from './components'
import { useSecuritySettings } from '@/hooks/useSecuritySettings'

export function SecuritySettings() {
  const {
    sessions,
    sortBy,
    sortOrder,
    hoveredStatus,
    sessionTimeout,
    isLoading,
    error,
    onSort,
    onTerminateSession,
    onRestoreSession,
    onHoveredStatusChange,
    onSessionTimeoutChange
  } = useSecuritySettings()

  return (
    <div className="space-y-4">
      <div className="bg-card rounded-lg border p-3">
        <h4 className="text-sm font-semibold mb-3 text-primary">Session Management</h4>
        <div className="space-y-0">
          <SettingRow 
            label="Session timeout"
            children={
              <select 
                value={sessionTimeout}
                onChange={(e) => onSessionTimeoutChange(e.target.value)}
                className="px-2 py-1 border border-input rounded text-sm bg-background min-w-16"
              >
                <option value="30m">30 minutes</option>
                <option value="1h">1 hour</option>
                <option value="4h">4 hours</option>
                <option value="8h">8 hours</option>
                <option value="24h">24 hours</option>
              </select>
            }
          />
        </div>
      </div>
      
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <p className="text-sm text-red-600">Failed to load sessions: {error}</p>
        </div>
      )}
      
      {isLoading ? (
        <div className="bg-card rounded-lg border p-8 text-center">
          <p className="text-sm text-muted-foreground">Loading sessions...</p>
        </div>
      ) : (
        <SessionTable 
          sessions={sessions}
          sortBy={sortBy}
          sortOrder={sortOrder}
          hoveredStatus={hoveredStatus}
          onSort={onSort}
          onTerminateSession={onTerminateSession}
          onRestoreSession={onRestoreSession}
          onHoveredStatusChange={onHoveredStatusChange}
        />
      )}
    </div>
  )
}