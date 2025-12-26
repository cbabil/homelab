/**
 * JWT Utilities Tests
 * 
 * Test suite for JWT utility functions including encoding, decoding,
 * parsing, and validation helpers.
 */

import { describe, it, expect } from 'vitest'
import {
  base64URLEncode,
  base64URLDecode,
  base64URLEncodeJSON,
  base64URLDecodeJSON,
  parseJWT,
  getTokenExpiration,
  isTokenExpired,
  getTimeToExpiration,
  getTokenId,
  getUserIdFromToken,
  isValidJWTPayload,
  generateJTI,
  validateTokenTiming,
  sanitizeTokenForLogging,
  compareJWTPayloads,
  extractTokenMetadata
} from '../jwtUtils'
import type { JWTHeader, JWTPayload } from '@/types/jwt'

describe('JWT Utilities', () => {
  describe('Base64URL Encoding/Decoding', () => {
    it('should encode and decode ArrayBuffer correctly', () => {
      const input = new TextEncoder().encode('Hello, World!')
      const encoded = base64URLEncode(input.buffer)
      const decoded = base64URLDecode(encoded)
      const result = new TextDecoder().decode(decoded)
      
      expect(result).toBe('Hello, World!')
    })

    it('should handle empty input', () => {
      const empty = new ArrayBuffer(0)
      const encoded = base64URLEncode(empty)
      const decoded = base64URLDecode(encoded)
      
      expect(decoded.byteLength).toBe(0)
    })

    it('should produce URL-safe output', () => {
      const input = new Uint8Array([255, 255, 255])
      const encoded = base64URLEncode(input.buffer)
      
      expect(encoded).not.toContain('+')
      expect(encoded).not.toContain('/')
      expect(encoded).not.toContain('=')
    })

    it('should handle padding correctly', () => {
      const inputs = ['f', 'fo', 'foo', 'foob', 'fooba', 'foobar']
      
      for (const input of inputs) {
        const buffer = new TextEncoder().encode(input)
        const encoded = base64URLEncode(buffer.buffer)
        const decoded = base64URLDecode(encoded)
        const result = new TextDecoder().decode(decoded)
        
        expect(result).toBe(input)
      }
    })
  })

  describe('JSON Encoding/Decoding', () => {
    it('should encode and decode JSON objects', () => {
      const obj = { hello: 'world', number: 42, boolean: true }
      const encoded = base64URLEncodeJSON(obj)
      const decoded = base64URLDecodeJSON(encoded)
      
      expect(decoded).toEqual(obj)
    })

    it('should handle complex nested objects', () => {
      const complex = {
        user: {
          id: 123,
          preferences: {
            theme: 'dark',
            notifications: true
          }
        },
        array: [1, 2, 3],
        nullValue: null
      }
      
      const encoded = base64URLEncodeJSON(complex)
      const decoded = base64URLDecodeJSON(encoded)
      
      expect(decoded).toEqual(complex)
    })

    it('should throw on invalid base64URL input', () => {
      expect(() => base64URLDecodeJSON('invalid!')).toThrow()
    })
  })

  describe('JWT Parsing', () => {
    const mockHeader: JWTHeader = { alg: 'HS256', typ: 'JWT' }
    const mockPayload: JWTPayload = {
      iss: 'test',
      sub: 'user123',
      aud: 'app',
      exp: Math.floor(Date.now() / 1000) + 3600,
      iat: Math.floor(Date.now() / 1000),
      jti: 'token123',
      id: 'user123',
      username: 'testuser',
      email: 'test@example.com',
      role: 'user',
      sessionId: 'session123',
      ipAddress: '127.0.0.1',
      userAgent: 'test',
      startTime: Math.floor(Date.now() / 1000),
      lastActivity: Math.floor(Date.now() / 1000),
      tokenType: 'access',
      scope: ['read'],
      authMethod: 'password',
      riskLevel: 'low'
    }

    function createToken(header = mockHeader, payload = mockPayload): string {
      const h = base64URLEncodeJSON(header)
      const p = base64URLEncodeJSON(payload)
      return `${h}.${p}.signature`
    }

    it('should parse valid JWT', () => {
      const token = createToken()
      const jwt = parseJWT(token)
      
      expect(jwt).toBeTruthy()
      expect(jwt?.header).toEqual(mockHeader)
      expect(jwt?.payload).toEqual(mockPayload)
      expect(jwt?.signature).toBe('signature')
    })

    it('should return null for malformed tokens', () => {
      const malformedTokens = [
        '',
        'invalid',
        'header.payload',
        'header.payload.signature.extra'
      ]

      for (const token of malformedTokens) {
        expect(parseJWT(token)).toBeNull()
      }
    })

    it('should return null for invalid JSON', () => {
      const invalidToken = 'invalid_json.invalid_json.signature'
      expect(parseJWT(invalidToken)).toBeNull()
    })

    it('should validate header structure', () => {
      const invalidHeader = { alg: 'RS256', typ: 'JWT' }
      const token = createToken(invalidHeader)
      expect(parseJWT(token)).toBeNull()
    })
  })

  describe('Token Information Extraction', () => {
    const mockPayload: JWTPayload = {
      iss: 'test',
      sub: 'user123',
      aud: 'app',
      exp: Math.floor(Date.now() / 1000) + 3600,
      iat: Math.floor(Date.now() / 1000),
      jti: 'token123',
      id: 'user123',
      username: 'testuser',
      email: 'test@example.com',
      role: 'user',
      sessionId: 'session123',
      ipAddress: '127.0.0.1',
      userAgent: 'test',
      startTime: Math.floor(Date.now() / 1000),
      lastActivity: Math.floor(Date.now() / 1000),
      tokenType: 'access',
      scope: ['read'],
      authMethod: 'password',
      riskLevel: 'low'
    }

    function createTestToken(payload = mockPayload): string {
      const header = base64URLEncodeJSON({ alg: 'HS256', typ: 'JWT' })
      const p = base64URLEncodeJSON(payload)
      return `${header}.${p}.signature`
    }

    it('should extract token expiration', () => {
      const token = createTestToken()
      const exp = getTokenExpiration(token)
      
      expect(exp).toBe(mockPayload.exp)
    })

    it('should detect expired tokens', () => {
      const expiredPayload = { ...mockPayload, exp: Math.floor(Date.now() / 1000) - 3600 }
      const token = createTestToken(expiredPayload)
      
      expect(isTokenExpired(token)).toBe(true)
    })

    it('should detect non-expired tokens', () => {
      const token = createTestToken()
      expect(isTokenExpired(token)).toBe(false)
    })

    it('should calculate time to expiration', () => {
      const futureExp = Math.floor(Date.now() / 1000) + 1800 // 30 minutes
      const futurePayload = { ...mockPayload, exp: futureExp }
      const token = createTestToken(futurePayload)
      const timeToExp = getTimeToExpiration(token)
      
      expect(timeToExp).toBeGreaterThan(1799000) // ~30 minutes in ms
      expect(timeToExp).toBeLessThanOrEqual(1800000)
    })

    it('should extract token ID', () => {
      const token = createTestToken()
      const jti = getTokenId(token)
      
      expect(jti).toBe(mockPayload.jti)
    })

    it('should extract user ID', () => {
      const token = createTestToken()
      const userId = getUserIdFromToken(token)
      
      expect(userId).toBe(mockPayload.sub)
    })

    it('should return null for invalid tokens', () => {
      expect(getTokenExpiration('invalid')).toBeNull()
      expect(getTokenId('invalid')).toBeNull()
      expect(getUserIdFromToken('invalid')).toBeNull()
    })
  })

  describe('JWT Payload Validation', () => {
    const validPayload: JWTPayload = {
      iss: 'test',
      sub: 'user123',
      aud: 'app',
      exp: Math.floor(Date.now() / 1000) + 3600,
      iat: Math.floor(Date.now() / 1000),
      jti: 'token123',
      id: 'user123',
      username: 'testuser',
      email: 'test@example.com',
      role: 'user',
      sessionId: 'session123',
      ipAddress: '127.0.0.1',
      userAgent: 'test',
      startTime: Math.floor(Date.now() / 1000),
      lastActivity: Math.floor(Date.now() / 1000),
      tokenType: 'access',
      scope: ['read'],
      authMethod: 'password',
      riskLevel: 'low'
    }

    it('should validate complete payload', () => {
      expect(isValidJWTPayload(validPayload)).toBe(true)
    })

    it('should reject missing required claims', () => {
      const requiredClaims = ['iss', 'sub', 'aud', 'exp', 'iat', 'jti', 'id', 'username', 'email', 'role', 'sessionId', 'tokenType', 'scope']
      
      for (const claim of requiredClaims) {
        const invalidPayload = { ...validPayload }
        delete (invalidPayload as any)[claim]
        
        expect(isValidJWTPayload(invalidPayload)).toBe(false)
      }
    })

    it('should reject invalid types', () => {
      expect(isValidJWTPayload(null)).toBe(false)
      expect(isValidJWTPayload('string')).toBe(false)
      expect(isValidJWTPayload(123)).toBe(false)
      expect(isValidJWTPayload([])).toBe(false)
    })

    it('should reject invalid role values', () => {
      const invalidRole = { ...validPayload, role: 'invalid' }
      expect(isValidJWTPayload(invalidRole)).toBe(false)
    })
  })

  describe('Token Timing Validation', () => {
    it('should validate current token timing', () => {
      const now = Math.floor(Date.now() / 1000)
      const payload: JWTPayload = {
        exp: now + 3600,
        iat: now - 60,
        // ... other required fields
      } as JWTPayload

      const result = validateTokenTiming(payload)
      expect(result.isValid).toBe(true)
    })

    it('should reject expired tokens', () => {
      const now = Math.floor(Date.now() / 1000)
      const payload: JWTPayload = {
        exp: now - 3600,
        iat: now - 7200,
        // ... other required fields
      } as JWTPayload

      const result = validateTokenTiming(payload)
      expect(result.isValid).toBe(false)
      expect(result.error).toContain('expired')
    })

    it('should reject tokens issued in future', () => {
      const now = Math.floor(Date.now() / 1000)
      const payload: JWTPayload = {
        exp: now + 7200,
        iat: now + 3600,
        // ... other required fields
      } as JWTPayload

      const result = validateTokenTiming(payload)
      expect(result.isValid).toBe(false)
      expect(result.error).toContain('future')
    })

    it('should respect clock tolerance', () => {
      const now = Math.floor(Date.now() / 1000)
      const payload: JWTPayload = {
        exp: now - 15, // 15 seconds expired
        iat: now - 3600,
        // ... other required fields
      } as JWTPayload

      // Should fail with default tolerance
      expect(validateTokenTiming(payload, 30).isValid).toBe(true)
      
      // Should pass with higher tolerance
      expect(validateTokenTiming(payload, 10).isValid).toBe(false)
    })
  })

  describe('Utility Functions', () => {
    it('should generate unique JTIs', () => {
      const jti1 = generateJTI()
      const jti2 = generateJTI()
      
      expect(jti1).not.toBe(jti2)
      expect(jti1).toMatch(/^[a-z0-9-]+$/i)
      expect(jti2).toMatch(/^[a-z0-9-]+$/i)
    })

    it('should sanitize tokens for logging', () => {
      const header = base64URLEncodeJSON({ alg: 'HS256', typ: 'JWT' })
      const payload = base64URLEncodeJSON({
        iss: 'test',
        sub: 'user123',
        email: 'secret@example.com',
        password: 'secret'
      })
      const token = `${header}.${payload}.signature`

      const sanitized = sanitizeTokenForLogging(token)
      
      expect(sanitized).toHaveProperty('payload.sub', 'user123')
      expect(sanitized).not.toHaveProperty('payload.email')
      expect(sanitized).not.toHaveProperty('payload.password')
    })

    it('should compare JWT payloads', () => {
      const payload1 = { sub: 'user1', exp: 123 }
      const payload2 = { sub: 'user1', exp: 123 }
      const payload3 = { sub: 'user2', exp: 123 }

      const token1 = `header.${base64URLEncodeJSON(payload1)}.sig`
      const token2 = `header.${base64URLEncodeJSON(payload2)}.sig`
      const token3 = `header.${base64URLEncodeJSON(payload3)}.sig`

      expect(compareJWTPayloads(token1, token2)).toBe(true)
      expect(compareJWTPayloads(token1, token3)).toBe(false)
    })

    it('should extract token metadata', () => {
      const payload = {
        jti: 'token123',
        sub: 'user123',
        tokenType: 'access',
        role: 'user'
      }
      
      const token = `header.${base64URLEncodeJSON(payload)}.sig`
      const metadata = extractTokenMetadata(token)
      
      expect(metadata).toMatchObject({
        jti: 'token123',
        sub: 'user123',
        tokenType: 'access',
        role: 'user'
      })
    })
  })
})