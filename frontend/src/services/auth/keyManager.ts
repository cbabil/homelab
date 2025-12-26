/**
 * JWT Key Management Service
 * 
 * Secure key generation, storage, and rotation using Web Crypto API.
 * Implements PBKDF2 key derivation and IndexedDB encrypted storage.
 */

import type { 
  CryptoKeyInfo, 
  SecureKeyStorage
} from '@/types/jwt'

interface StoredKeyData {
  id: string
  keyData: ArrayBuffer
  info: CryptoKeyInfo
  salt: ArrayBuffer
}

class KeyManager implements SecureKeyStorage {
  private readonly dbName = 'homelab-jwt-keys'
  private readonly dbVersion = 3 // Incremented to force key regeneration
  private readonly keyStoreName = 'keys'
  private readonly fingerprintVersion = 'v3' // Track fingerprint method version
  private activeKeyId: string | null = null
  private db: IDBDatabase | null = null
  private fallbackKeyCache: CryptoKey | null = null
  private retryCount = 0
  private readonly maxRetries = 2

  /**
   * Initialize key manager and database
   */
  async initialize(): Promise<void> {
    await this.openDatabase()
    await this.ensureActiveKey()
  }

  /**
   * Generate new HMAC key for JWT signing
   */
  async generateHMACKey(): Promise<{ key: CryptoKey; keyId: string }> {
    const keyId = this.generateKeyId()
    
    const key = await crypto.subtle.generateKey(
      {
        name: 'HMAC',
        hash: 'SHA-256'
      },
      true, // extractable for storage
      ['sign', 'verify']
    )

    const keyInfo: CryptoKeyInfo = {
      id: keyId,
      algorithm: 'HMAC',
      usage: ['sign', 'verify'],
      createdAt: Date.now(),
      isActive: false
    }

    await this.storeKey(keyId, key, keyInfo)
    return { key, keyId }
  }

  /**
   * Store encrypted key in IndexedDB
   */
  async storeKey(keyId: string, key: CryptoKey, info?: CryptoKeyInfo): Promise<void> {
    if (!this.db) throw new Error('Database not initialized')

    // Export key for storage
    const keyData = await crypto.subtle.exportKey('raw', key)
    
    // Generate salt for encryption
    const salt = crypto.getRandomValues(new Uint8Array(16)).buffer
    
    // Derive encryption key from master password
    const encryptionKey = await this.deriveEncryptionKey(salt)
    
    // Encrypt the key data
    const iv = crypto.getRandomValues(new Uint8Array(12)).buffer
    const encryptedData = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      encryptionKey,
      keyData
    )

    const storedData: StoredKeyData = {
      id: keyId,
      keyData: encryptedData,
      info: info || {
        id: keyId,
        algorithm: 'HMAC',
        usage: ['sign', 'verify'],
        createdAt: Date.now(),
        isActive: false
      },
      salt
    }

    // Store in IndexedDB
    const transaction = this.db.transaction([this.keyStoreName], 'readwrite')
    const store = transaction.objectStore(this.keyStoreName)
    
    await new Promise<void>((resolve, reject) => {
      const request = store.put({ ...storedData, iv })
      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Retrieve and decrypt key from storage
   */
  async getKey(keyId: string): Promise<CryptoKey | null> {
    if (!this.db) throw new Error('Database not initialized')

    const transaction = this.db.transaction([this.keyStoreName], 'readonly')
    const store = transaction.objectStore(this.keyStoreName)

    const storedData = await new Promise<StoredKeyData & { iv: ArrayBuffer } | null>(
      (resolve, reject) => {
        const request = store.get(keyId)
        request.onsuccess = () => resolve(request.result || null)
        request.onerror = () => reject(request.error)
      }
    )

    if (!storedData) return null

    try {
      // Derive decryption key
      const encryptionKey = await this.deriveEncryptionKey(storedData.salt)
      
      // Decrypt key data
      const decryptedData = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: storedData.iv },
        encryptionKey,
        storedData.keyData
      )

      // Import the decrypted key
      const key = await crypto.subtle.importKey(
        'raw',
        decryptedData,
        { name: 'HMAC', hash: 'SHA-256' },
        false,
        ['sign', 'verify']
      )
      
      // Reset retry count on success
      this.retryCount = 0
      return key
    } catch (error) {
      console.error('Failed to decrypt key:', error)
      return await this.handleDecryptionFailure(keyId)
    }
  }

  /**
   * List all stored keys
   */
  async listKeys(): Promise<CryptoKeyInfo[]> {
    if (!this.db) throw new Error('Database not initialized')

    const transaction = this.db.transaction([this.keyStoreName], 'readonly')
    const store = transaction.objectStore(this.keyStoreName)

    return new Promise((resolve, reject) => {
      const request = store.getAll()
      request.onsuccess = () => {
        const keys = request.result.map((item: StoredKeyData) => item.info)
        resolve(keys)
      }
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Delete key from storage
   */
  async deleteKey(keyId: string): Promise<void> {
    if (!this.db) throw new Error('Database not initialized')

    const transaction = this.db.transaction([this.keyStoreName], 'readwrite')
    const store = transaction.objectStore(this.keyStoreName)

    await new Promise<void>((resolve, reject) => {
      const request = store.delete(keyId)
      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Rotate keys - generate new active key and mark old as inactive
   */
  async rotateKeys(): Promise<string> {
    // Generate new key
    const { keyId } = await this.generateHMACKey()
    
    // Mark old active key as inactive
    if (this.activeKeyId) {
      await this.setKeyActive(this.activeKeyId, false)
    }
    
    // Set new key as active
    await this.setKeyActive(keyId, true)
    this.activeKeyId = keyId

    console.log('[KeyManager] Key rotation completed:', keyId)
    return keyId
  }

  /**
   * Get current active key with fallback mechanism
   */
  async getActiveKey(): Promise<{ key: CryptoKey; keyId: string } | null> {
    if (!this.activeKeyId) {
      await this.ensureActiveKey()
    }

    if (!this.activeKeyId) {
      return await this.getFallbackKey()
    }

    const key = await this.getKey(this.activeKeyId)
    if (key) {
      return { key, keyId: this.activeKeyId }
    }
    
    // If main key fails, try fallback
    return await this.getFallbackKey()
  }

  /**
   * Derive encryption key from master password using PBKDF2
   */
  private async deriveEncryptionKey(salt: ArrayBuffer): Promise<CryptoKey> {
    // In production, this would use a proper master password
    // For demo, we use a derived key from browser fingerprint
    const masterPassword = await this.getMasterPassword()
    
    const keyMaterial = await crypto.subtle.importKey(
      'raw',
      new TextEncoder().encode(masterPassword),
      { name: 'PBKDF2' },
      false,
      ['deriveKey']
    )

    return await crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt,
        iterations: 100000,
        hash: 'SHA-256'
      },
      keyMaterial,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt', 'decrypt']
    )
  }

  /**
   * Get master password for key encryption
   */
  private async getMasterPassword(): Promise<string> {
    try {
      // Use only the most stable browser characteristics
      // Avoid dynamic values that can change between sessions
      const fingerprint = [
        navigator.userAgent,
        navigator.language,
        screen.width.toString(),
        screen.height.toString(),
        this.fingerprintVersion, // Version tracking for consistency
        'homelab-assistant-stable-key' // Static application salt
      ].join('|')

      const hashBuffer = await crypto.subtle.digest(
        'SHA-256', 
        new TextEncoder().encode(fingerprint)
      )
      
      return Array.from(new Uint8Array(hashBuffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('')
    } catch (error) {
      console.error('Failed to generate master password:', error)
      // Fallback to a simpler deterministic key
      return 'homelab-fallback-key-' + this.fingerprintVersion
    }
  }

  /**
   * Handle decryption failure with retry logic and fallback
   */
  private async handleDecryptionFailure(keyId: string): Promise<CryptoKey | null> {
    this.retryCount++
    
    if (this.retryCount <= this.maxRetries) {
      console.log(`[KeyManager] Retrying decryption (${this.retryCount}/${this.maxRetries})`)
      // Wait briefly before retry
      await new Promise(resolve => setTimeout(resolve, 100))
      return await this.getKey(keyId)
    }
    
    console.log('[KeyManager] Max retries exceeded, clearing corrupted keys...')
    await this.clearCorruptedKeys()
    return null
  }

  /**
   * Clear corrupted keys when decryption fails
   */
  private async clearCorruptedKeys(): Promise<void> {
    if (!this.db) return
    
    try {
      const transaction = this.db.transaction([this.keyStoreName], 'readwrite')
      const store = transaction.objectStore(this.keyStoreName)
      await store.clear()
      this.activeKeyId = null
      this.retryCount = 0
      console.log('[KeyManager] Cleared corrupted keys, will use fallback mechanism')
    } catch (error) {
      console.error('Failed to clear corrupted keys:', error)
    }
  }

  /**
   * Generate and cache a fallback key that doesn't require persistent storage
   */
  private async getFallbackKey(): Promise<{ key: CryptoKey; keyId: string } | null> {
    if (!this.fallbackKeyCache) {
      console.log('[KeyManager] Generating fallback in-memory key...')
      
      try {
        this.fallbackKeyCache = await crypto.subtle.generateKey(
          {
            name: 'HMAC',
            hash: 'SHA-256'
          },
          false, // Not extractable for security
          ['sign', 'verify']
        )
        console.log('[KeyManager] Fallback key generated successfully')
      } catch (error) {
        console.error('Failed to generate fallback key:', error)
        return null
      }
    }
    
    return {
      key: this.fallbackKeyCache,
      keyId: 'fallback-key-' + Date.now()
    }
  }

  /**
   * Generate unique key identifier
   */
  private generateKeyId(): string {
    const timestamp = Date.now().toString(36)
    const random = Math.random().toString(36).substring(2)
    return `key_${timestamp}_${random}`
  }

  /**
   * Open IndexedDB database
   */
  private async openDatabase(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion)
      
      request.onerror = () => reject(request.error)
      request.onsuccess = () => {
        this.db = request.result
        resolve()
      }
      
      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result
        
        if (!db.objectStoreNames.contains(this.keyStoreName)) {
          db.createObjectStore(this.keyStoreName, { keyPath: 'id' })
        }
      }
    })
  }

  /**
   * Ensure an active key exists
   */
  private async ensureActiveKey(): Promise<void> {
    const keys = await this.listKeys()
    const activeKey = keys.find(k => k.isActive)
    
    if (activeKey) {
      this.activeKeyId = activeKey.id
      return
    }

    // No active key found, generate one
    const { keyId } = await this.generateHMACKey()
    await this.setKeyActive(keyId, true)
    this.activeKeyId = keyId
  }

  /**
   * Set key active status
   */
  private async setKeyActive(keyId: string, isActive: boolean): Promise<void> {
    if (!this.db) throw new Error('Database not initialized')

    const transaction = this.db.transaction([this.keyStoreName], 'readwrite')
    const store = transaction.objectStore(this.keyStoreName)

    const storedData = await new Promise<StoredKeyData>((resolve, reject) => {
      const request = store.get(keyId)
      request.onsuccess = () => resolve(request.result)
      request.onerror = () => reject(request.error)
    })

    if (storedData) {
      storedData.info.isActive = isActive
      await new Promise<void>((resolve, reject) => {
        const request = store.put(storedData)
        request.onsuccess = () => resolve()
        request.onerror = () => reject(request.error)
      })
    }
  }
}

export const keyManager = new KeyManager()
export default keyManager