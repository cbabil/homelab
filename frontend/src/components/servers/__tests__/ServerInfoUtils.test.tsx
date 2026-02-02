/**
 * ServerInfoUtils Test Suite
 *
 * Tests for the utility functions that format server information.
 */

import { describe, it, expect } from 'vitest'
import { formatUptime } from '../ServerInfoUtils'

describe('formatUptime', () => {
  describe('undefined/empty input', () => {
    it('should return undefined for undefined input', () => {
      expect(formatUptime(undefined)).toBeUndefined()
    })

    it('should return undefined for empty string', () => {
      expect(formatUptime('')).toBeUndefined()
    })
  })

  describe('days format', () => {
    it('should return uptime as-is when it contains days', () => {
      expect(formatUptime('5 days, 12:34')).toBe('5 days, 12:34')
    })

    it('should return uptime as-is for various days formats', () => {
      expect(formatUptime('1 days ago')).toBe('1 days ago')
    })
  })

  describe('time format HH:MM', () => {
    it('should format hours and minutes', () => {
      expect(formatUptime('12:34')).toBe('12h 34m')
    })

    it('should format only minutes when hours is 0', () => {
      expect(formatUptime('00:45')).toBe('45m')
    })

    it('should format only hours when minutes is 0', () => {
      expect(formatUptime('05:00')).toBe('5h')
    })

    it('should handle single digit values', () => {
      expect(formatUptime('1:5')).toBe('1h 5m')
    })
  })

  describe('other formats', () => {
    it('should return uptime as-is for unrecognized format', () => {
      expect(formatUptime('up 5 hours')).toBe('up 5 hours')
    })

    it('should return uptime as-is for text format', () => {
      expect(formatUptime('running')).toBe('running')
    })
  })
})
