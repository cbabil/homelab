/**
 * Timezone Service - IANA timezone support with regional grouping and caching
 */

import {
  TimezoneInfo, TimezoneGroup, TimezoneRegion, TimezoneConversion,
  SystemTimezone, DEFAULT_TIMEZONE_FORMAT, POPULAR_TIMEZONES
} from '@/types/timezone'

class TimezoneService {
  private timezones: TimezoneInfo[] = []
  private timezonesCache = new Map<string, TimezoneInfo>()
  private systemTimezone: SystemTimezone | null = null
  private initialized = false

  async initialize(): Promise<void> {
    if (this.initialized) return
    this.loadTimezones()
    this.systemTimezone = this.detectSystemTimezone()
    this.initialized = true
  }

  getTimezoneGroups(): TimezoneGroup[] {
    this.ensureInitialized()
    const groups = new Map<TimezoneRegion, TimezoneInfo[]>()
    this.timezones.forEach(tz => {
      if (!groups.has(tz.region)) groups.set(tz.region, [])
      groups.get(tz.region)!.push(tz)
    })
    return Array.from(groups.entries()).map(([region, timezones]) => ({
      region, timezones: timezones.sort((a, b) => a.name.localeCompare(b.name))
    }))
  }

  getPopularTimezones(): TimezoneInfo[] {
    this.ensureInitialized()
    return POPULAR_TIMEZONES.map(id => this.timezonesCache.get(id)).filter(Boolean) as TimezoneInfo[]
  }

  getTimezoneById(id: string): TimezoneInfo | null {
    this.ensureInitialized()
    return this.timezonesCache.get(id) || null
  }

  getSystemTimezone(): SystemTimezone {
    this.ensureInitialized()
    return this.systemTimezone || { id: 'UTC', detected: false, supported: true }
  }

  convertTimezone(date: Date, from: string, to: string, opts = DEFAULT_TIMEZONE_FORMAT): TimezoneConversion {
    const sourceDate = new Date(date)
    const targetDate = new Date(date.toLocaleString('en-US', { timeZone: to }))
    return {
      sourceDate, targetDate, sourceTimezone: from, targetTimezone: to,
      formattedTime: this.formatDateForTimezone(targetDate, to, opts)
    }
  }

  formatDateForTimezone(date: Date, timezone: string, opts = DEFAULT_TIMEZONE_FORMAT): string {
    const formatOpts: Intl.DateTimeFormatOptions = {
      timeZone: timezone, hour12: opts.format12Hour, hour: '2-digit', minute: '2-digit',
      second: opts.showSeconds ? '2-digit' : undefined
    }
    let formatted = date.toLocaleString('en-US', formatOpts)

    if (opts.showOffset || opts.showAbbreviation) {
      const tz = this.getTimezoneById(timezone)
      if (tz) {
        const parts = []
        if (opts.showOffset) parts.push(this.formatOffset(tz.offset))
        if (opts.showAbbreviation) parts.push(tz.abbreviation)
        formatted += ` (${parts.join(' ')})`
      }
    }
    return formatted
  }

  private loadTimezones(): void {
    const data = [
      ['UTC', 'UTC', 'UTC', 'Pacific', 'Coordinated Universal Time', 'UTC'],
      ['America/New_York', 'Eastern Time', 'EST/EDT', 'America', 'United States', 'US'],
      ['America/Chicago', 'Central Time', 'CST/CDT', 'America', 'United States', 'US'],
      ['America/Denver', 'Mountain Time', 'MST/MDT', 'America', 'United States', 'US'],
      ['America/Los_Angeles', 'Pacific Time', 'PST/PDT', 'America', 'United States', 'US'],
      ['Europe/London', 'Greenwich Mean Time', 'GMT/BST', 'Europe', 'United Kingdom', 'GB'],
      ['Europe/Paris', 'Central European Time', 'CET/CEST', 'Europe', 'France', 'FR'],
      ['Europe/Berlin', 'Central European Time', 'CET/CEST', 'Europe', 'Germany', 'DE'],
      ['Asia/Tokyo', 'Japan Standard Time', 'JST', 'Asia', 'Japan', 'JP'],
      ['Asia/Shanghai', 'China Standard Time', 'CST', 'Asia', 'China', 'CN'],
      ['Asia/Seoul', 'Korea Standard Time', 'KST', 'Asia', 'South Korea', 'KR'],
      ['Australia/Sydney', 'Australian Eastern Time', 'AEST/AEDT', 'Australia', 'Australia', 'AU']
    ]

    this.timezones = data.map(([id, name, abbr, region, country, code]) => ({
      id, name, abbreviation: abbr, region: region as TimezoneRegion, country, countryCode: code,
      isPopular: true, offset: this.calcOffset(id)
    }))
    this.timezones.forEach(tz => this.timezonesCache.set(tz.id, tz))
  }

  private calcOffset(tzId: string): number {
    const now = new Date()
    const utc = new Date(now.getTime() + now.getTimezoneOffset() * 60000)
    const target = new Date(utc.toLocaleString('en-US', { timeZone: tzId }))
    return Math.round((target.getTime() - utc.getTime()) / 60000)
  }

  private detectSystemTimezone(): SystemTimezone {
    try {
      const detected = Intl.DateTimeFormat().resolvedOptions().timeZone
      const supported = this.timezonesCache.has(detected)
      return { id: detected, detected: true, supported, fallback: supported ? undefined : 'UTC' }
    } catch {
      return { id: 'UTC', detected: false, supported: true }
    }
  }

  private formatOffset(minutes: number): string {
    const sign = minutes >= 0 ? '+' : '-'
    const h = Math.floor(Math.abs(minutes) / 60)
    const m = Math.abs(minutes) % 60
    return `UTC${sign}${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`
  }

  private ensureInitialized(): void {
    if (!this.initialized) throw new Error('TimezoneService not initialized. Call initialize() first.')
  }
}

export const timezoneService = new TimezoneService()
export default timezoneService