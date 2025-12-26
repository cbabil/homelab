/**
 * JWT Service Tests
 * 
 * Comprehensive test suite for JWT service functionality including
 * token generation, validation, refresh, revocation, and security.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import jwtService from '../jwtService'
import keyManager from '../keyManager'
import { parseJWT, generateJTI } from '@/utils/jwtUtils'
import type { JWTGenerationOptions } from '@/types/jwt'

// Mock IndexedDB for testing
const mockIndexedDB = {
  open: vi.fn(() => ({
    result: {
      transaction: vi.fn(() => ({
        objectStore: vi.fn(() => ({
          put: vi.fn(),
          get: vi.fn(),
          delete: vi.fn(),
          getAll: vi.fn(() => ({ result: [] }))
        }))
      })),
      objectStoreNames: { contains: vi.fn(() => false) },
      createObjectStore: vi.fn()
    },
    onsuccess: null,
    onerror: null,
    onupgradeneeded: null
  }))
}

// Setup test environment
beforeEach(async () => {
  // Mock browser APIs
  global.indexedDB = mockIndexedDB as any
  
  // Mock crypto API properly
  Object.defineProperty(global, 'crypto', {
    value: {
      subtle: {
        generateKey: vi.fn(async () => ({}) as CryptoKey),
        importKey: vi.fn(async () => ({}) as CryptoKey),
        exportKey: vi.fn(async () => new ArrayBuffer(32)),
        sign: vi.fn(async () => new ArrayBuffer(32)),
        verify: vi.fn(async () => true),
        encrypt: vi.fn(async () => new ArrayBuffer(48)),
        decrypt: vi.fn(async () => new ArrayBuffer(32)),
        deriveKey: vi.fn(async () => ({}) as CryptoKey),
        digest: vi.fn(async () => new ArrayBuffer(32))
      },
      getRandomValues: vi.fn((arr: Uint8Array) => {
        for (let i = 0; i < arr.length; i++) {
          arr[i] = Math.floor(Math.random() * 256)
        }
        return arr
      })
    },
    writable: true,
    configurable: true
  })

  // Reset services
  await jwtService.initialize()
})

describe('JWT Service', () => {
  const mockOptions: JWTGenerationOptions = {
    userId: 'user123',
    username: 'testuser',
    email: 'test@example.com',
    role: 'user',
    sessionId: 'session123',
    ipAddress: '192.168.1.1',
    userAgent: 'Test Browser',
    tokenType: 'access',
    scope: ['read', 'write']
  }

  describe('Token Generation', () => {
    it('should generate valid access token', async () => {
      const token = await jwtService.generateToken(mockOptions)
      
      expect(token).toBeTruthy()
      expect(typeof token).toBe('string')
      expect(token.split('.').length).toBe(3)

      const jwt = parseJWT(token)
      expect(jwt).toBeTruthy()
      expect(jwt?.payload.sub).toBe(mockOptions.userId)
      expect(jwt?.payload.tokenType).toBe('access')
    })

    it('should generate valid refresh token', async () => {
      const refreshOptions = { ...mockOptions, tokenType: 'refresh' as const }
      const token = await jwtService.generateToken(refreshOptions)
      
      const jwt = parseJWT(token)
      expect(jwt?.payload.tokenType).toBe('refresh')
    })

    it('should include all required claims', async () => {
      const token = await jwtService.generateToken(mockOptions)
      const jwt = parseJWT(token)
      
      expect(jwt?.payload).toMatchObject({
        iss: expect.any(String),
        sub: mockOptions.userId,
        aud: expect.any(String),
        exp: expect.any(Number),
        iat: expect.any(Number),
        jti: expect.any(String),
        id: mockOptions.userId,
        username: mockOptions.username,
        email: mockOptions.email,
        role: mockOptions.role,
        sessionId: mockOptions.sessionId,
        tokenType: mockOptions.tokenType
      })
    })

    it('should set correct expiration times', async () => {
      const accessToken = await jwtService.generateToken({
        ...mockOptions,
        tokenType: 'access'
      })
      
      const refreshToken = await jwtService.generateToken({
        ...mockOptions,
        tokenType: 'refresh'
      })

      const accessJWT = parseJWT(accessToken)
      const refreshJWT = parseJWT(refreshToken)
      
      expect(accessJWT?.payload.exp).toBeLessThan(refreshJWT?.payload.exp || 0)
    })
  })

  describe('Token Validation', () => {
    it('should validate valid token', async () => {
      const token = await jwtService.generateToken(mockOptions)
      const validation = await jwtService.validateToken(token)
      
      expect(validation.isValid).toBe(true)
      expect(validation.payload).toBeTruthy()
      expect(validation.error).toBeUndefined()
    })

    it('should reject malformed token', async () => {
      const validation = await jwtService.validateToken('invalid.token')
      
      expect(validation.isValid).toBe(false)
      expect(validation.error?.code).toBe('MALFORMED')
    })

    it('should reject token with wrong algorithm', async () => {
      // Create token with wrong algorithm manually
      const header = { alg: 'RS256', typ: 'JWT' }
      const payload = { sub: 'test', exp: Date.now() + 3600 }
      const token = `${btoa(JSON.stringify(header))}.${btoa(JSON.stringify(payload))}.signature`
      
      const validation = await jwtService.validateToken(token)
      expect(validation.isValid).toBe(false)
      expect(validation.error?.code).toBe('ALGORITHM_MISMATCH')
    })

    it('should detect expired tokens', async () => {
      // Mock expired token by manipulating time
      const expiredOptions = { ...mockOptions }
      const token = await jwtService.generateToken(expiredOptions)
      
      // Mock token with past expiration
      const jwt = parseJWT(token)
      if (jwt) {
        jwt.payload.exp = Math.floor(Date.now() / 1000) - 3600 // 1 hour ago
        const mockToken = `${btoa(JSON.stringify(jwt.header))}.${btoa(JSON.stringify(jwt.payload))}.signature`
        
        const validation = await jwtService.validateToken(mockToken)
        expect(validation.isValid).toBe(false)
        expect(validation.error?.code).toBe('EXPIRED')
      }
    })
  })

  describe('Token Refresh', () => {
    it('should refresh valid refresh token', async () => {
      const refreshToken = await jwtService.generateToken({
        ...mockOptions,
        tokenType: 'refresh'
      })

      const tokenPair = await jwtService.refreshToken(refreshToken)
      
      expect(tokenPair.accessToken).toBeTruthy()
      expect(tokenPair.refreshToken).toBeTruthy()
      expect(tokenPair.expiresIn).toBeGreaterThan(0)
      expect(tokenPair.refreshExpiresIn).toBeGreaterThan(tokenPair.expiresIn)
    })

    it('should reject access token for refresh', async () => {
      const accessToken = await jwtService.generateToken({
        ...mockOptions,
        tokenType: 'access'
      })

      await expect(jwtService.refreshToken(accessToken))
        .rejects.toThrow('not a refresh token')
    })

    it('should preserve user information in refreshed tokens', async () => {
      const refreshToken = await jwtService.generateToken({
        ...mockOptions,
        tokenType: 'refresh'
      })

      const tokenPair = await jwtService.refreshToken(refreshToken)
      const newAccessJWT = parseJWT(tokenPair.accessToken)
      
      expect(newAccessJWT?.payload.username).toBe(mockOptions.username)
      expect(newAccessJWT?.payload.email).toBe(mockOptions.email)
      expect(newAccessJWT?.payload.role).toBe(mockOptions.role)
    })
  })

  describe('Token Revocation', () => {
    it('should revoke token and prevent validation', async () => {
      const token = await jwtService.generateToken(mockOptions)
      
      // Token should be valid initially
      let validation = await jwtService.validateToken(token)
      expect(validation.isValid).toBe(true)
      
      // Revoke token
      await jwtService.revokeToken(token, 'logout')
      
      // Token should be invalid after revocation
      validation = await jwtService.validateToken(token)
      expect(validation.isValid).toBe(false)
      expect(validation.error?.code).toBe('REVOKED')
    })

    it('should handle different revocation reasons', async () => {
      const token = await jwtService.generateToken(mockOptions)
      
      const reasons: Array<'logout' | 'revoke' | 'security'> = ['logout', 'revoke', 'security']
      
      for (const reason of reasons) {
        const testToken = await jwtService.generateToken(mockOptions)
        await expect(jwtService.revokeToken(testToken, reason))
          .resolves.not.toThrow()
      }
    })
  })

  describe('Token Utilities', () => {
    it('should decode token without validation', async () => {
      const token = await jwtService.generateToken(mockOptions)
      const decoded = jwtService.decodeToken(token)
      
      expect(decoded).toBeTruthy()
      expect(decoded?.payload.sub).toBe(mockOptions.userId)
    })

    it('should calculate remaining TTL', async () => {
      const token = await jwtService.generateToken(mockOptions)
      const ttl = jwtService.getTokenTTL(token)
      
      expect(ttl).toBeGreaterThan(0)
      expect(ttl).toBeLessThanOrEqual(3600) // Default access token TTL
    })

    it('should return zero TTL for expired tokens', async () => {
      const jwt = parseJWT(await jwtService.generateToken(mockOptions))
      if (jwt) {
        jwt.payload.exp = Math.floor(Date.now() / 1000) - 3600
        const expiredToken = `${btoa(JSON.stringify(jwt.header))}.${btoa(JSON.stringify(jwt.payload))}.signature`
        
        const ttl = jwtService.getTokenTTL(expiredToken)
        expect(ttl).toBe(0)
      }
    })
  })

  describe('Security Features', () => {
    it('should generate unique JWT IDs', async () => {
      const jti1 = generateJTI()
      const jti2 = generateJTI()
      
      expect(jti1).not.toBe(jti2)
      expect(jti1).toMatch(/^[a-z0-9-]+$/i)
    })

    it('should include security metadata in tokens', async () => {
      const token = await jwtService.generateToken(mockOptions)
      const jwt = parseJWT(token)
      
      expect(jwt?.payload).toMatchObject({
        tokenType: expect.any(String),
        scope: expect.any(Array),
        authMethod: expect.any(String),
        riskLevel: expect.any(String)
      })
    })

    it('should validate audience and issuer', async () => {
      const token = await jwtService.generateToken(mockOptions)
      const jwt = parseJWT(token)
      
      expect(jwt?.payload.aud).toBeTruthy()
      expect(jwt?.payload.iss).toBeTruthy()
    })

    it('should handle clock tolerance in validation', async () => {
      const token = await jwtService.generateToken(mockOptions)
      const jwt = parseJWT(token)
      
      if (jwt) {
        // Token issued slightly in future (within tolerance)
        jwt.payload.iat = Math.floor(Date.now() / 1000) + 15 // 15 seconds in future
        const futureToken = `${btoa(JSON.stringify(jwt.header))}.${btoa(JSON.stringify(jwt.payload))}.signature`
        
        const validation = await jwtService.validateToken(futureToken)
        expect(validation.isValid).toBe(true) // Should pass due to clock tolerance
      }
    })
  })

  describe('Error Handling', () => {
    it('should handle missing signing keys gracefully', async () => {
      // Mock key manager to return null
      vi.spyOn(keyManager, 'getActiveKey').mockResolvedValue(null)
      
      await expect(jwtService.generateToken(mockOptions))
        .rejects.toThrow('No active signing key')
    })

    it('should handle malformed tokens gracefully', async () => {
      const malformedTokens = [
        '',
        'invalid',
        'header.payload',
        'header.payload.signature.extra'
      ]

      for (const token of malformedTokens) {
        const validation = await jwtService.validateToken(token)
        expect(validation.isValid).toBe(false)
        expect(validation.error?.code).toBe('MALFORMED')
      }
    })

    it('should handle crypto errors gracefully', async () => {
      // Mock crypto failure
      vi.spyOn(crypto.subtle, 'sign').mockRejectedValue(new Error('Crypto error'))
      
      await expect(jwtService.generateToken(mockOptions))
        .rejects.toThrow()
    })
  })
})