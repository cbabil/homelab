/**
 * useRetentionSettings Hook Tests
 *
 * Unit tests for the retention settings hook including:
 * - Settings initialization and state management
 * - MCP backend integration
 * - Preview cleanup operations and validation
 * - Settings validation
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useRetentionSettings } from '../useRetentionSettings'
import type { RetentionSettings, RetentionOperationResult } from '@/types/settings'

// Mock MCP client
const mockCallTool = vi.fn()
const mockMcpClient = {
  callTool: mockCallTool
}

// Mock MCP Provider
vi.mock('@/providers/MCPProvider', () => ({
  useMCP: vi.fn(() => ({
    client: mockMcpClient,
    isConnected: true
  }))
}))

// Mock system logger
vi.mock('@/services/systemLogger', () => ({
  mcpLogger: {
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    debug: vi.fn()
  }
}))

// Default retention settings for tests
const defaultSettings: RetentionSettings = {
  log_retention: 30,
  data_retention: 90,
  last_updated: new Date().toISOString(),
  updated_by_user_id: 'test-user'
}

describe('useRetentionSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Default successful response for get_retention_settings
    mockCallTool.mockResolvedValue({
      success: true,
      data: { data: defaultSettings }
    })
  })

  describe('Initialization', () => {
    it('should load settings from MCP backend on mount', async () => {
      const { result } = renderHook(() => useRetentionSettings())

      expect(result.current.isLoading).toBe(true)

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(mockCallTool).toHaveBeenCalledWith('get_retention_settings', { params: {} })
      expect(result.current.settings).toEqual(defaultSettings)
      expect(result.current.error).toBeNull()
    })

    it('should use default settings when MCP fails', async () => {
      mockCallTool.mockResolvedValue({
        success: false,
        error: 'Failed to load'
      })

      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.settings).toEqual({
        log_retention: 30,
        data_retention: 90
      })
    })

    it('should report backend connected status', async () => {
      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.isBackendConnected).toBe(true)
    })
  })

  describe('Update Settings', () => {
    it('should update log retention via MCP', async () => {
      const updatedSettings: RetentionSettings = {
        ...defaultSettings,
        log_retention: 60
      }

      mockCallTool
        .mockResolvedValueOnce({ success: true, data: { data: defaultSettings } }) // Initial load
        .mockResolvedValueOnce({ success: true, data: { data: updatedSettings } }) // Update

      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      await act(async () => {
        await result.current.updateRetentionSettings({ log_retention: 60 })
      })

      expect(mockCallTool).toHaveBeenCalledWith('update_retention_settings', {
        params: {
          log_retention: 60,
          data_retention: 90
        }
      })

      expect(result.current.settings?.log_retention).toBe(60)
    })

    it('should update data retention via MCP', async () => {
      const updatedSettings: RetentionSettings = {
        ...defaultSettings,
        data_retention: 180
      }

      mockCallTool
        .mockResolvedValueOnce({ success: true, data: { data: defaultSettings } })
        .mockResolvedValueOnce({ success: true, data: { data: updatedSettings } })

      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      await act(async () => {
        await result.current.updateRetentionSettings({ data_retention: 180 })
      })

      expect(result.current.settings?.data_retention).toBe(180)
    })

    it('should handle update failures', async () => {
      mockCallTool
        .mockResolvedValueOnce({ success: true, data: { data: defaultSettings } })
        .mockResolvedValueOnce({ success: false, data: { error: 'Update failed' } })

      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      const updateResult = await act(async () => {
        return result.current.updateRetentionSettings({ log_retention: 60 })
      })

      expect(updateResult?.success).toBe(false)
      expect(result.current.error).toBe('Update failed')
    })

    it('should validate settings before update', async () => {
      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Clear the initial load call
      mockCallTool.mockClear()

      // Try to update with invalid values (below minimum)
      await act(async () => {
        await result.current.updateRetentionSettings({ log_retention: 5 })
      })

      // Should not call update tool with invalid values
      expect(mockCallTool).not.toHaveBeenCalled()
      expect(result.current.error).toContain('Log retention must be between')
    })
  })

  describe('Preview Cleanup Operations', () => {
    it('should call preview cleanup via MCP', async () => {
      const previewResult = {
        retention_type: 'access_logs',
        affected_records: 150,
        oldest_record_date: '2024-01-01T00:00:00Z',
        newest_record_date: '2024-01-15T00:00:00Z',
        estimated_space_freed_mb: 0.15,
        cutoff_date: '2024-01-01T00:00:00Z'
      }

      mockCallTool
        .mockResolvedValueOnce({ success: true, data: { data: defaultSettings } })
        .mockResolvedValueOnce({ success: true, data: { data: previewResult } })

      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      let previewResponse: RetentionOperationResult | undefined
      await act(async () => {
        previewResponse = await result.current.previewCleanup('access_logs')
      })

      expect(mockCallTool).toHaveBeenCalledWith('preview_retention_cleanup', {
        params: { retention_type: 'access_logs' }
      })

      expect(previewResponse!.success).toBe(true)
      expect(result.current.previewResult?.logEntriesAffected).toBe(150)
    })

    it('should handle preview failure', async () => {
      mockCallTool
        .mockResolvedValueOnce({ success: true, data: { data: defaultSettings } })
        .mockResolvedValueOnce({ success: false, data: { message: 'Preview failed' } })

      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      let previewResponse: RetentionOperationResult | undefined
      await act(async () => {
        previewResponse = await result.current.previewCleanup()
      })

      expect(previewResponse!.success).toBe(false)
      expect(result.current.error).toBe('Preview failed')
    })
  })

  describe('Perform Cleanup Operations', () => {
    it('should get CSRF token and perform cleanup', async () => {
      const csrfToken = 'test-csrf-token-12345678901234567890'
      const cleanupResult = {
        operation_id: 'cleanup-123',
        retention_type: 'access_logs',
        records_affected: 150,
        space_freed_mb: 0.15,
        duration_seconds: 2.5,
        start_time: '2024-01-01T00:00:00Z',
        end_time: '2024-01-01T00:00:03Z'
      }

      mockCallTool
        .mockResolvedValueOnce({ success: true, data: { data: defaultSettings } }) // Load
        .mockResolvedValueOnce({ success: true, data: { data: { csrf_token: csrfToken } } }) // CSRF
        .mockResolvedValueOnce({ success: true, data: { data: cleanupResult } }) // Cleanup

      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      let cleanupResponse: RetentionOperationResult | undefined
      await act(async () => {
        cleanupResponse = await result.current.performCleanup('access_logs')
      })

      expect(mockCallTool).toHaveBeenCalledWith('get_csrf_token', { params: {} })
      expect(mockCallTool).toHaveBeenCalledWith('perform_retention_cleanup', {
        params: {
          retention_type: 'access_logs',
          csrf_token: csrfToken
        }
      })

      expect(cleanupResponse!.success).toBe(true)
      expect(cleanupResponse!.deletedCounts?.access_logs).toBe(150)
    })

    it('should fail if CSRF token cannot be obtained', async () => {
      mockCallTool
        .mockResolvedValueOnce({ success: true, data: { data: defaultSettings } })
        .mockResolvedValueOnce({ success: false }) // CSRF fails

      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      let cleanupResponse: RetentionOperationResult | undefined
      await act(async () => {
        cleanupResponse = await result.current.performCleanup()
      })

      expect(cleanupResponse!.success).toBe(false)
      expect(cleanupResponse!.error).toContain('CSRF token')
    })
  })

  describe('Data Validation and Limits', () => {
    it('should provide correct validation limits', async () => {
      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.limits).toEqual({
        LOG_MIN: 7,
        LOG_MAX: 365,
        DATA_MIN: 7,
        DATA_MAX: 365
      })
    })

    it('should validate settings against limits', async () => {
      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Test log retention validation - below minimum
      let validation = result.current.validateRetentionSettings({
        log_retention: 5,
        data_retention: 30
      })
      expect(validation.valid).toBe(false)

      // Test log retention validation - above maximum
      validation = result.current.validateRetentionSettings({
        log_retention: 400,
        data_retention: 30
      })
      expect(validation.valid).toBe(false)

      // Test valid log retention
      validation = result.current.validateRetentionSettings({
        log_retention: 30,
        data_retention: 30
      })
      expect(validation.valid).toBe(true)

      // Test data retention validation - below minimum
      validation = result.current.validateRetentionSettings({
        log_retention: 30,
        data_retention: 5
      })
      expect(validation.valid).toBe(false)

      // Test data retention validation - above maximum
      validation = result.current.validateRetentionSettings({
        log_retention: 30,
        data_retention: 400
      })
      expect(validation.valid).toBe(false)

      // Test valid data retention
      validation = result.current.validateRetentionSettings({
        log_retention: 30,
        data_retention: 365
      })
      expect(validation.valid).toBe(true)
    })
  })
})
