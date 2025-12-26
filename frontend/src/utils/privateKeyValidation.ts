/**
 * Private Key Validation Utilities
 * 
 * Utilities for validating private key files and content.
 */

export interface ValidationResult {
  isValid: boolean
  error?: string
}

export function validatePrivateKeyFile(file: File): ValidationResult {
  // Validate file size (max 10KB for private keys)
  if (file.size > 10 * 1024) {
    return {
      isValid: false,
      error: 'Private key file must be less than 10KB'
    }
  }

  // Validate file extension
  const validExtensions = ['.pem', '.key', '.id_rsa', '.openssh', '.ppk']
  const hasValidExtension = validExtensions.some(ext => 
    file.name.toLowerCase().endsWith(ext)
  ) || !file.name.includes('.')

  if (!hasValidExtension) {
    return {
      isValid: false,
      error: 'Please select a valid private key file (.pem, .key, .id_rsa, .openssh)'
    }
  }

  return { isValid: true }
}

export function validatePrivateKeyContent(content: string): ValidationResult {
  const privateKeyMarkers = [
    '-----BEGIN PRIVATE KEY-----',
    '-----BEGIN RSA PRIVATE KEY-----',
    '-----BEGIN DSA PRIVATE KEY-----',
    '-----BEGIN EC PRIVATE KEY-----',
    '-----BEGIN OPENSSH PRIVATE KEY-----'
  ]
  
  const isValid = privateKeyMarkers.some(marker => content.includes(marker))
  
  return {
    isValid,
    error: isValid ? undefined : 'File does not appear to contain a valid private key'
  }
}

export function readFileContent(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(reader.error)
    reader.readAsText(file)
  })
}