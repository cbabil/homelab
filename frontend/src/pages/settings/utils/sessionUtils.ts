/**
 * Session Utilities
 * 
 * Utility functions for session management and sorting.
 */

import type { Session, SortKey } from '../types'

export function getStatusSortOrder(status: string): number {
  switch (status) {
    case 'active': return 1
    case 'idle': return 2
    case 'expired': return 3
    default: return 4
  }
}

export function sortSessions(
  sessions: Session[], 
  sortBy: SortKey, 
  sortOrder: 'asc' | 'desc'
): Session[] {
  return [...sessions].sort((a, b) => {
    let comparison = 0
    
    switch (sortBy) {
      case 'status':
        comparison = getStatusSortOrder(a.status) - getStatusSortOrder(b.status)
        break
      case 'sessionId':
        comparison = a.id.localeCompare(b.id)
        break
      case 'started':
        comparison = a.started.getTime() - b.started.getTime()
        break
      case 'lastActivity':
        comparison = a.lastActivity.getTime() - b.lastActivity.getTime()
        break
      case 'location':
        comparison = a.location.localeCompare(b.location)
        break
      case 'actions': {
        const aIsCurrent = a.id.includes('7a2f') ? 1 : 0
        const bIsCurrent = b.id.includes('7a2f') ? 1 : 0
        comparison = bIsCurrent - aIsCurrent || getStatusSortOrder(a.status) - getStatusSortOrder(b.status)
        break
      }
    }
    
    return sortOrder === 'asc' ? comparison : -comparison
  })
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'active':
      return 'bg-green-500'
    case 'idle':
      return 'bg-orange-500'
    case 'expired':
      return 'bg-red-500'
    default:
      return 'bg-gray-400'
  }
}