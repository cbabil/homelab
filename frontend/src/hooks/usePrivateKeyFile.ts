/**
 * Private Key File Hook
 * 
 * Handles private key file selection, validation, and state management.
 */

import { useState, useEffect } from 'react'
import { 
  validatePrivateKeyFile, 
  validatePrivateKeyContent, 
  readFileContent 
} from '@/utils/privateKeyValidation'

export function usePrivateKeyFile(value?: string, onChange?: (content: string) => void) {
  const [selectedFile, setSelectedFile] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [hasExistingKey, setHasExistingKey] = useState(false)
  const [wasExistingKey, setWasExistingKey] = useState(false)

  // Check if we have an existing key (editing mode)
  useEffect(() => {
    if (value === '***EXISTING_KEY***') {
      setHasExistingKey(true)
      setWasExistingKey(true)
      setSelectedFile('')
    } else {
      setHasExistingKey(false)
      setWasExistingKey(false)
    }
  }, [value])

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    
    if (!file) {
      setSelectedFile('')
      setError('')
      setHasExistingKey(false)
      return
    }

    // Validate file
    const fileValidation = validatePrivateKeyFile(file)
    if (!fileValidation.isValid) {
      setError(fileValidation.error!)
      event.target.value = ''
      return
    }

    setIsLoading(true)
    setError('')

    try {
      const content = await readFileContent(file)
      
      // Validate content
      const contentValidation = validatePrivateKeyContent(content)
      if (!contentValidation.isValid) {
        setError(contentValidation.error!)
        event.target.value = ''
        return
      }

      setSelectedFile(file.name)
      setHasExistingKey(false) // Hide existing key indicator
      onChange?.(content)
    } catch {
      setError('Failed to read file. Please try again.')
      event.target.value = ''
    } finally {
      setIsLoading(false)
    }
  }

  return {
    selectedFile,
    isLoading,
    error,
    hasExistingKey,
    wasExistingKey,
    handleFileSelect
  }
}