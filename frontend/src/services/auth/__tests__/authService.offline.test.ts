/**
 * AuthService Offline Fallback Tests
 *
 * Verifies that authentication succeeds with local credentials when the MCP
 * server cannot be reached and that invalid credentials are rejected.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

describe('AuthService offline fallback', () => {
  const connectMock = vi.fn()
  const callToolMock = vi.fn()

  const mockJwtService = {
    initialize: vi.fn().mockResolvedValue(undefined),
    generateToken: vi.fn(async ({ tokenType }: { tokenType: string }) => `${tokenType}-token`),
    refreshToken: vi.fn().mockResolvedValue({
      accessToken: 'refreshed-access-token',
      refreshToken: 'refreshed-refresh-token',
      expiresIn: 3600
    }),
    decodeToken: vi.fn().mockReturnValue({
      payload: {
        id: 'offline-admin',
        username: 'admin',
        email: 'admin@homelab.local',
        role: 'admin',
        preferences: {}
      }
    }),
    validateToken: vi.fn().mockResolvedValue({ isValid: true }),
    revokeToken: vi.fn().mockResolvedValue(undefined)
  }

  beforeEach(() => {
    vi.resetModules()
    vi.doUnmock('@/services/auth/authService')

    connectMock.mockRejectedValue(new Error('Failed to connect to MCP server'))
    callToolMock.mockResolvedValue({
      success: false,
      error: 'Failed to connect to MCP server'
    })

    mockJwtService.generateToken.mockImplementation(async ({ tokenType }: { tokenType: string }) => `${tokenType}-token`)
    mockJwtService.refreshToken.mockResolvedValue({
      accessToken: 'refreshed-access-token',
      refreshToken: 'refreshed-refresh-token',
      expiresIn: 3600
    })

    vi.mock('@/services/auth/jwtService', () => ({ jwtService: mockJwtService }))
    vi.mock('@/services/mcpClient', () => ({
      HomelabMCPClient: vi.fn().mockImplementation(() => ({
        connect: connectMock,
        callTool: callToolMock,
        isConnected: vi.fn().mockReturnValue(false)
      }))
    }))
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('allows login with offline credentials when MCP connection fails', async () => {
    const { authService } = await import('../authService')

    const response = await authService.login({
      username: 'admin',
      password: 'HomeLabAdmin123!'
    })

    expect(response.user.username).toBe('admin')
    expect(response.token).toBe('access-token')
    expect(connectMock).toHaveBeenCalled()
    expect(callToolMock).not.toHaveBeenCalled()
  })

  it('rejects invalid credentials in offline mode', async () => {
    const { authService } = await import('../authService')

    await expect(
      authService.login({ username: 'admin', password: 'wrong-password' })
    ).rejects.toThrow('Invalid username or password')

    expect(connectMock).toHaveBeenCalled()
  })

  it('falls back to deterministic tokens when JWT generation fails', async () => {
    connectMock.mockRejectedValue(new Error('Connection refused'))
    mockJwtService.generateToken.mockRejectedValue(new Error('crypto unavailable'))

    const { authService } = await import('../authService')

    const response = await authService.login({
      username: 'user',
      password: 'HomeLabUser123!'
    })

    expect(response.token).toMatch(/^offline-access-/)
    expect(response.refreshToken).toMatch(/^offline-refresh-/)
  })
})
