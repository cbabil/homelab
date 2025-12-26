/**
 * Session Row Component
 * 
 * Individual session row with status, actions, and hover tooltip.
 */

import { Trash2, RotateCcw, Shield, User } from 'lucide-react'
import { cn } from '@/utils/cn'
import type { Session } from '../types'
import { formatDateTime, formatTimeAgo, getStatusColor } from '../utils'
import { useAuth } from '@/providers/AuthProvider'

interface SessionRowProps {
  session: Session
  hoveredStatus: string | null
  onTerminateSession: (sessionId: string) => void
  onRestoreSession: (sessionId: string) => void
  onHoveredStatusChange: (sessionId: string | null) => void
}

export function SessionRow({
  session,
  hoveredStatus,
  onTerminateSession,
  onRestoreSession,
  onHoveredStatusChange
}: SessionRowProps) {
  // Get current user from auth context
  const { user } = useAuth()
  
  // Determine if this is the current session by checking if location contains "Current"
  // In a real implementation, this would be a proper flag from the session data
  const isCurrentSession = session.location.includes('Current') || session.location.includes('current')
  
  // Check if user is admin
  const isAdmin = user?.role === 'admin'
  
  // Can terminate session if user is admin and it's not the current session
  const canTerminate = isAdmin && !isCurrentSession && session.status === 'active'

  return (
    <tr className="hover:bg-muted/50 transition-colors">
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="flex items-center justify-center">
          <div 
            className="relative p-2 cursor-help"
            onMouseEnter={() => onHoveredStatusChange(session.id)}
            onMouseLeave={() => onHoveredStatusChange(null)}
          >
            <div className={cn("w-2 h-2 rounded-full", getStatusColor(session.status))}></div>
            {hoveredStatus === session.id && (
              <div className="absolute left-full top-1/2 transform -translate-y-1/2 ml-1 px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap z-10">
                {session.status.charAt(0).toUpperCase() + session.status.slice(1)}
                <div className="absolute right-full top-1/2 transform -translate-y-1/2 border-2 border-transparent border-r-gray-900"></div>
              </div>
            )}
          </div>
        </div>
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <span className="text-sm font-mono text-foreground">{session.id}</span>
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <span className="text-sm text-muted-foreground">
          {formatDateTime(session.started)}
        </span>
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <span className="text-sm text-muted-foreground">
          {formatTimeAgo(session.lastActivity)}
        </span>
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <span className="text-sm font-mono text-foreground">{session.ip}</span>
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="flex items-center justify-center space-x-2">
          {/* Check if this is the current session */}
          {isCurrentSession ? (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 rounded-md border border-blue-200 dark:border-blue-800">
              <User className="h-3 w-3" />
              <span className="text-xs font-medium">You</span>
            </div>
          ) : (
            <>
              {session.status === 'expired' ? (
                isAdmin ? (
                  <button
                    onClick={() => onRestoreSession(session.id)}
                    className="inline-flex items-center justify-center p-1.5 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors rounded-md hover:bg-blue-50 dark:hover:bg-blue-950"
                    title="Restore session"
                  >
                    <RotateCcw className="h-4 w-4" />
                  </button>
                ) : (
                  <span className="text-xs text-muted-foreground px-2 py-1">Expired</span>
                )
              ) : (
                canTerminate ? (
                  <button
                    onClick={() => onTerminateSession(session.id)}
                    className="inline-flex items-center justify-center p-1.5 text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 transition-colors rounded-md hover:bg-red-50 dark:hover:bg-red-950"
                    title="Terminate session"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                ) : (
                  <span className="text-xs text-muted-foreground px-2 py-1">
                    {!isAdmin ? 'Admin Only' : 'Active'}
                  </span>
                )
              )}
            </>
          )}
        </div>
      </td>
    </tr>
  )
}