/**
 * Private Key File Input Component
 *
 * Handles private key file selection with a proper button style.
 */

import { useRef } from 'react'
import { Upload, FileKey, CheckCircle2, RefreshCw } from 'lucide-react'
import { Box, Stack, Typography, CircularProgress } from '@mui/material'
import { Button } from '@/components/ui/Button'
import { usePrivateKeyFile } from '@/hooks/usePrivateKeyFile'

interface PrivateKeyFileInputProps {
  value?: string
  onChange: (content: string) => void
  required?: boolean
  showExistingKey?: boolean
  onUpdateKey?: () => void
  disabled?: boolean
}

export function PrivateKeyFileInput({
  value,
  onChange,
  required = false,
  showExistingKey = false,
  onUpdateKey,
  disabled = false
}: PrivateKeyFileInputProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const {
    selectedFile,
    isLoading,
    error,
    handleFileSelect
  } = usePrivateKeyFile(value, onChange)

  const handleButtonClick = () => {
    fileInputRef.current?.click()
  }

  // Show existing key state
  if (showExistingKey && value === '***EXISTING_KEY***') {
    return (
      <Box>
        <Typography variant="body2" fontWeight={500} sx={{ mb: 1 }}>
          Private Key
        </Typography>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            p: 1.5,
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            bgcolor: 'action.hover'
          }}
        >
          <Stack direction="row" spacing={1} alignItems="center" sx={{ color: 'success.main' }}>
            <FileKey size={16} />
            <Typography variant="body2">Private key configured</Typography>
            <CheckCircle2 size={14} />
          </Stack>
          {onUpdateKey && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onUpdateKey}
              disabled={disabled}
              leftIcon={<RefreshCw size={14} />}
            >
              Change
            </Button>
          )}
        </Box>
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="body2" fontWeight={500} sx={{ mb: 1 }}>
        Private Key
      </Typography>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pem,.key,.id_rsa,.openssh,.ppk,id_*"
        onChange={handleFileSelect}
        required={required && !selectedFile}
        style={{ display: 'none' }}
      />

      {/* File selection button */}
      <Button
        type="button"
        variant="outline"
        onClick={handleButtonClick}
        disabled={isLoading || disabled}
        fullWidth
        leftIcon={
          isLoading ? (
            <CircularProgress size={16} color="inherit" />
          ) : selectedFile ? (
            <FileKey size={16} />
          ) : (
            <Upload size={16} />
          )
        }
      >
        {isLoading
          ? 'Reading file...'
          : selectedFile
            ? selectedFile
            : 'Select private key file'}
      </Button>

      {/* Status messages */}
      {error && (
        <Typography variant="caption" color="error.main" sx={{ mt: 1, display: 'block' }}>
          {error}
        </Typography>
      )}

      {selectedFile && !error && (
        <Typography variant="caption" color="success.main" sx={{ mt: 1, display: 'block' }}>
          File loaded successfully
        </Typography>
      )}
    </Box>
  )
}
