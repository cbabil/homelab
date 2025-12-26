/**
 * Server Info Utilities
 * 
 * Utility functions for formatting server information.
 */

export function formatUptime(uptime?: string): string | undefined {
  if (!uptime) return undefined
  
  // Handle various uptime formats from different systems
  if (uptime.includes('days')) {
    return uptime
  }
  
  // Convert simple format like "12:34" to "12 hours, 34 minutes"
  const timeMatch = uptime.match(/^(\d+):(\d+)$/)
  if (timeMatch) {
    const [, hours, minutes] = timeMatch
    const h = parseInt(hours)
    const m = parseInt(minutes)
    
    if (h === 0) return `${m}m`
    if (m === 0) return `${h}h`
    return `${h}h ${m}m`
  }
  
  return uptime
}