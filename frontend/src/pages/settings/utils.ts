/**
 * Settings Utilities
 * 
 * Shared utility functions for settings components.
 */

// Re-export session utilities
export { sortSessions, getStatusSortOrder, getStatusColor } from './utils/sessionUtils'


interface ValidationResult {
  isValid: boolean
  error: string
}

/**
 * Enhanced JSON validation function for MCP configuration
 */
export function validateMcpConfig(jsonString: string): ValidationResult {
  if (!jsonString.trim()) {
    return { isValid: false, error: 'JSON cannot be empty' }
  }
  
  try {
    const parsed = JSON.parse(jsonString)
    
    // Validate structure - should be an object
    if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
      return { isValid: false, error: 'Configuration must be a valid JSON object' }
    }
    
    // Basic validation for MCP config structure
    if (parsed.mcpServers && typeof parsed.mcpServers !== 'object') {
      return { isValid: false, error: 'mcpServers must be an object' }
    }
    
    return { isValid: true, error: '' }
  } catch (e) {
    if (e instanceof SyntaxError) {
      const match = e.message.match(/at position (\d+)/)
      const position = match ? parseInt(match[1]) : null
      
      if (position !== null) {
        const lines = jsonString.substring(0, position).split('\n')
        const lineNumber = lines.length
        const columnNumber = lines[lines.length - 1].length + 1
        return { 
          isValid: false, 
          error: `JSON syntax error at line ${lineNumber}, column ${columnNumber}: ${e.message}` 
        }
      }
      
      return { isValid: false, error: `JSON syntax error: ${e.message}` }
    }
    
    return { isValid: false, error: 'Invalid JSON format' }
  }
}

/**
 * Format date/time for display in tables
 */
export function formatDateTime(date: Date): string {
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()
  const isYesterday = date.toDateString() === new Date(now.getTime() - 24 * 60 * 60 * 1000).toDateString()
  
  if (isToday) {
    return `Today ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}`
  } else if (isYesterday) {
    return `Yesterday ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}`
  } else {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true })
  }
}

/**
 * Format time elapsed since a date
 */
export function formatTimeAgo(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMinutes = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMinutes < 1) return 'Just now'
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return `${diffDays}d ago`
}