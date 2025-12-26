/**
 * Existing Key Indicator Component
 * 
 * Shows read-only indication of existing private key with option to replace.
 */

import React from 'react'
import { Lock } from 'lucide-react'
import { FileInputButton } from './FileInputButton'

interface ExistingKeyIndicatorProps {
  onFileSelect: (event: React.ChangeEvent<HTMLInputElement>) => void
  isLoading: boolean
}

export function ExistingKeyIndicator({ onFileSelect, isLoading }: ExistingKeyIndicatorProps) {
  return (
    <div className="space-y-3">
      <div className="w-full px-3 py-2 border border-input rounded-lg bg-muted/50 
                      flex items-center justify-center">
        <div className="flex items-center space-x-2 text-muted-foreground">
          <Lock className="h-4 w-4" />
          <span className="text-sm">Private key configured</span>
        </div>
      </div>
      
      <div className="text-xs text-muted-foreground text-center">
        Select a new file to replace the existing private key
      </div>
      
      <FileInputButton
        accept=".pem,.key,.id_rsa,.openssh,.ppk"
        onChange={onFileSelect}
        selectedFile=""
        isLoading={isLoading}
        required={false}
      />
    </div>
  )
}