/**
 * Private Key File Input Component
 * 
 * Handles private key file selection and reading for SSH authentication.
 */

import { AlertCircle } from 'lucide-react'
import { FileInputButton } from './FileInputButton'
import { ExistingKeyIndicator } from './ExistingKeyIndicator'
import { usePrivateKeyFile } from '@/hooks/usePrivateKeyFile'

interface PrivateKeyFileInputProps {
  value?: string
  onChange: (content: string) => void
  required?: boolean
}

export function PrivateKeyFileInput({ 
  value,
  onChange, 
  required = false 
}: PrivateKeyFileInputProps) {
  const {
    selectedFile,
    isLoading,
    error,
    hasExistingKey,
    wasExistingKey,
    handleFileSelect
  } = usePrivateKeyFile(value, onChange)

  return (
    <div>
      <label className="block text-sm font-medium mb-1">Private Key File</label>
      
      {hasExistingKey && !selectedFile ? (
        <ExistingKeyIndicator 
          onFileSelect={handleFileSelect}
          isLoading={isLoading}
        />
      ) : (
        <FileInputButton
          accept=".pem,.key,.id_rsa,.openssh,.ppk"
          onChange={handleFileSelect}
          selectedFile={selectedFile}
          isLoading={isLoading}
          required={required}
        />
      )}

      {error && (
        <div className="mt-2 flex items-center space-x-2 text-destructive text-sm">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}
      
      {selectedFile && !error && (
        <p className="mt-2 text-sm text-muted-foreground">
          {wasExistingKey && !hasExistingKey ? 'New file loaded successfully' : 'File loaded successfully'}
        </p>
      )}
    </div>
  )
}