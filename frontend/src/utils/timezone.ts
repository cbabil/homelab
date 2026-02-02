/**
 * Timezone Utilities
 *
 * Utility functions for formatting dates and times with timezone support.
 * Integrates with the timezone service and user settings.
 */

import { timezoneService } from '@/services/timezoneService'
import { TimezoneFormatOptions, DEFAULT_TIMEZONE_FORMAT } from '@/types/timezone'

/**
 * Format a date in the user's selected timezone
 */
export function formatDateInTimezone(
  date: Date | string | number,
  timezone: string = 'UTC',
  options: TimezoneFormatOptions = DEFAULT_TIMEZONE_FORMAT
): string {
  const dateObj = new Date(date)

  if (isNaN(dateObj.getTime())) {
    return 'Invalid Date'
  }

  return timezoneService.formatDateForTimezone(dateObj, timezone, options)
}

/**
 * Convert a date between timezones
 */
export function convertBetweenTimezones(
  date: Date | string | number,
  fromTimezone: string,
  toTimezone: string,
  options: TimezoneFormatOptions = DEFAULT_TIMEZONE_FORMAT
) {
  const dateObj = new Date(date)

  if (isNaN(dateObj.getTime())) {
    return null
  }

  return timezoneService.convertTimezone(dateObj, fromTimezone, toTimezone, options)
}

/**
 * Format a date for display with short format
 */
export function formatDateTimeShort(
  date: Date | string | number,
  timezone: string = 'UTC'
): string {
  return formatDateInTimezone(date, timezone, {
    showOffset: false,
    showAbbreviation: false,
    format12Hour: true,
    showSeconds: false
  })
}

/**
 * Format a date for display with full format
 */
export function formatDateTimeFull(
  date: Date | string | number,
  timezone: string = 'UTC'
): string {
  return formatDateInTimezone(date, timezone, {
    showOffset: true,
    showAbbreviation: true,
    format12Hour: false,
    showSeconds: true
  })
}

/**
 * Format a date for logs with consistent format
 */
export function formatLogTimestamp(
  date: Date | string | number,
  timezone: string = 'UTC'
): string {
  const dateObj = new Date(date)

  if (isNaN(dateObj.getTime())) {
    return 'Invalid Date'
  }

  // Use consistent format for logs: YYYY-MM-DD HH:mm:ss (TZ)
  const formatted = dateObj.toLocaleString('en-CA', {
    timeZone: timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })

  // Get timezone abbreviation - try timezone service first, fallback to simple abbreviation
  let tzDisplay = timezone
  try {
    const tz = timezoneService.getTimezoneById(timezone)
    tzDisplay = tz?.abbreviation || timezone
  } catch (_error) {
    // If timezone service isn't initialized, use a simple approach
    if (timezone === 'America/New_York') {
      tzDisplay = 'EST/EDT'
    } else if (timezone === 'America/Los_Angeles') {
      tzDisplay = 'PST/PDT'
    } else if (timezone === 'America/Chicago') {
      tzDisplay = 'CST/CDT'
    } else {
      tzDisplay = timezone
    }
  }

  return `${formatted} (${tzDisplay})`
}

/**
 * Format a date as relative time (e.g., "2 hours ago", "3 days ago")
 */
export function formatRelativeTime(
  date: Date | string | number,
  _timezone: string = 'UTC'
): string {
  const dateObj = new Date(date)

  if (isNaN(dateObj.getTime())) {
    return 'Invalid Date'
  }

  const now = new Date()
  const diffMs = now.getTime() - dateObj.getTime()
  const diffSeconds = Math.floor(diffMs / 1000)
  const diffMinutes = Math.floor(diffSeconds / 60)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)
  const diffWeeks = Math.floor(diffDays / 7)
  const diffMonths = Math.floor(diffDays / 30)

  if (diffSeconds < 60) {
    return 'Just now'
  } else if (diffMinutes < 60) {
    return `${diffMinutes}m ago`
  } else if (diffHours < 24) {
    return `${diffHours}h ago`
  } else if (diffDays < 7) {
    return `${diffDays}d ago`
  } else if (diffWeeks < 4) {
    return `${diffWeeks}w ago`
  } else {
    return `${diffMonths}mo ago`
  }
}

/**
 * Get relative time string (e.g., "2 minutes ago")
 */
export function getRelativeTime(
  date: Date | string | number,
  timezone: string = 'UTC'
): string {
  const dateObj = new Date(date)

  if (isNaN(dateObj.getTime())) {
    return 'Invalid Date'
  }

  const now = new Date()
  const diffMs = now.getTime() - dateObj.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffSec < 60) {
    return 'Just now'
  } else if (diffMin < 60) {
    return `${diffMin} minute${diffMin !== 1 ? 's' : ''} ago`
  } else if (diffHour < 24) {
    return `${diffHour} hour${diffHour !== 1 ? 's' : ''} ago`
  } else if (diffDay < 7) {
    return `${diffDay} day${diffDay !== 1 ? 's' : ''} ago`
  } else {
    // For older dates, show the actual date in the user's timezone
    return formatDateTimeShort(dateObj, timezone)
  }
}

/**
 * Check if timezone service is initialized
 */
export function isTimezoneServiceReady(): boolean {
  try {
    // Try to get timezone groups to check if service is initialized
    timezoneService.getTimezoneGroups()
    return true
  } catch {
    return false
  }
}