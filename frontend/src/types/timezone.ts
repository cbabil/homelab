/**
 * Timezone Types
 *
 * Type definitions for timezone management including IANA timezone info,
 * regional grouping, and date formatting utilities.
 */

// Core timezone information interface
export interface TimezoneInfo {
  id: string // IANA timezone identifier (e.g., 'America/New_York')
  name: string // Human-readable name (e.g., 'Eastern Time')
  abbreviation: string // Common abbreviation (e.g., 'EST/EDT')
  offset: number // UTC offset in minutes
  region: TimezoneRegion // Geographic region
  country: string // Country name
  countryCode: string // ISO country code (e.g., 'US')
  isPopular: boolean // Commonly used timezone
}

// Geographic regions for timezone grouping
export type TimezoneRegion =
  | 'America'
  | 'Europe'
  | 'Asia'
  | 'Africa'
  | 'Australia'
  | 'Pacific'

// Timezone selection options with regional grouping
export interface TimezoneGroup {
  region: TimezoneRegion
  timezones: TimezoneInfo[]
}

// Date formatting options for timezone display
export interface TimezoneFormatOptions {
  showOffset: boolean
  showAbbreviation: boolean
  format12Hour: boolean
  showSeconds: boolean
}

// Timezone conversion result
export interface TimezoneConversion {
  sourceDate: Date
  targetDate: Date
  sourceTimezone: string
  targetTimezone: string
  formattedTime: string
}

// System timezone detection result
export interface SystemTimezone {
  id: string
  detected: boolean
  supported: boolean
  fallback?: string
}

// Timezone service configuration
export interface TimezoneServiceConfig {
  cacheTimeout: number // Cache timeout in milliseconds
  enableSystemDetection: boolean
  popularTimezonesOnly: boolean
}

// Popular timezone identifiers for quick access
export const POPULAR_TIMEZONES = [
  'America/New_York',
  'America/Los_Angeles',
  'America/Chicago',
  'America/Denver',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Asia/Seoul',
  'Australia/Sydney',
  'UTC'
] as const

// Default timezone formatting options
export const DEFAULT_TIMEZONE_FORMAT: TimezoneFormatOptions = {
  showOffset: true,
  showAbbreviation: true,
  format12Hour: false,
  showSeconds: false
}