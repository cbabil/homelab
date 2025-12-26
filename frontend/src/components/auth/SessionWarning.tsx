/**
 * Session Warning Component
 * 
 * Displays session expiry warnings with configurable actions.
 * Shows countdown and allows session extension or logout.
 */

import React from 'react'
import { AlertTriangle, Clock, X } from 'lucide-react'
import { cn } from '@/utils/cn'
import { SessionWarning as SessionWarningType } from '@/types/auth'

interface SessionWarningProps {
  warning: SessionWarningType
  onExtendSession?: () => void
  onLogout?: () => void
  onDismiss?: () => void
}

export function SessionWarning({ 
  warning, 
  onExtendSession, 
  onLogout, 
  onDismiss 
}: SessionWarningProps) {
  if (!warning.isShowing) {
    return null
  }

  const getWarningStyles = () => {
    switch (warning.warningLevel) {
      case 'critical':
        return {
          container: 'bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800',
          icon: 'text-red-600 dark:text-red-400',
          text: 'text-red-800 dark:text-red-200',
          button: 'bg-red-600 hover:bg-red-700 text-white'
        }
      case 'warning':
        return {
          container: 'bg-orange-50 border-orange-200 dark:bg-orange-950 dark:border-orange-800',
          icon: 'text-orange-600 dark:text-orange-400',
          text: 'text-orange-800 dark:text-orange-200',
          button: 'bg-orange-600 hover:bg-orange-700 text-white'
        }
      default:
        return {
          container: 'bg-blue-50 border-blue-200 dark:bg-blue-950 dark:border-blue-800',
          icon: 'text-blue-600 dark:text-blue-400',
          text: 'text-blue-800 dark:text-blue-200',
          button: 'bg-blue-600 hover:bg-blue-700 text-white'
        }
    }
  }

  const styles = getWarningStyles()
  const isUrgent = warning.minutesRemaining <= 1

  const formatTimeRemaining = () => {
    if (warning.minutesRemaining <= 0) {
      return 'Session has expired'
    } else if (warning.minutesRemaining === 1) {
      return '1 minute remaining'
    } else {
      return `${warning.minutesRemaining} minutes remaining`
    }
  }

  return (
    <div className={cn(
      'fixed top-4 right-4 max-w-md w-full border rounded-lg p-4 shadow-lg z-50',
      'animate-in slide-in-from-right-4 fade-in duration-300',
      styles.container
    )}>
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          {isUrgent ? (
            <AlertTriangle className={cn("h-5 w-5", styles.icon)} />
          ) : (
            <Clock className={cn("h-5 w-5", styles.icon)} />
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className={cn("text-sm font-medium", styles.text)}>
            {isUrgent ? 'Session Expired' : 'Session Expiring Soon'}
          </h3>
          <p className={cn("text-sm mt-1", styles.text)}>
            {formatTimeRemaining()}
          </p>
          
          <div className="flex items-center space-x-2 mt-3">
            {!isUrgent && onExtendSession && (
              <button
                onClick={onExtendSession}
                className={cn(
                  'px-3 py-1 text-xs font-medium rounded transition-colors',
                  styles.button
                )}
              >
                Extend Session
              </button>
            )}
            
            {onLogout && (
              <button
                onClick={onLogout}
                className="px-3 py-1 text-xs font-medium rounded border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors"
              >
                {isUrgent ? 'Login Again' : 'Logout'}
              </button>
            )}
          </div>
        </div>
        
        {onDismiss && !isUrgent && (
          <button
            onClick={onDismiss}
            className={cn(
              "flex-shrink-0 p-1 hover:bg-black/5 dark:hover:bg-white/5 rounded transition-colors",
              styles.text
            )}
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  )
}