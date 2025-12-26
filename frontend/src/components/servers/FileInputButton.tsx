/**
 * File Input Button Component
 * 
 * Styled file input with loading states and visual feedback.
 */

import React from 'react'
import { Upload, File } from 'lucide-react'

interface FileInputButtonProps {
  accept: string
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void
  selectedFile: string
  isLoading: boolean
  required?: boolean
}

export function FileInputButton({
  accept,
  onChange,
  selectedFile,
  isLoading,
  required = false
}: FileInputButtonProps) {
  return (
    <div className="relative">
      <input
        type="file"
        accept={accept}
        onChange={onChange}
        required={required}
        className="hidden"
        id="private-key-file"
      />
      
      <label
        htmlFor="private-key-file"
        className="w-full px-3 py-2 border border-input rounded-lg bg-background 
                   hover:bg-accent cursor-pointer flex items-center justify-center
                   focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2"
      >
        {isLoading ? (
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
            <span>Reading file...</span>
          </div>
        ) : selectedFile ? (
          <div className="flex items-center space-x-2">
            <File className="h-4 w-4" />
            <span className="text-sm truncate">{selectedFile}</span>
          </div>
        ) : (
          <div className="flex items-center space-x-2">
            <Upload className="h-4 w-4" />
            <span>Select private key file</span>
          </div>
        )}
      </label>
    </div>
  )
}