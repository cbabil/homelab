/**
 * Data Retention Settings Component
 *
 * Secure interface for configuring automatic data cleanup policies
 * with multi-step confirmation flows and preview capabilities.
 */

import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Box, Stack, Typography, Slider, TextField, Alert, Card } from '@mui/material'
import { SettingRow } from '../components'
import { useRetentionSettings } from '@/hooks/useRetentionSettings'
import { Button } from '@/components/ui/Button'

interface SliderWithInputProps {
  value: number
  min: number
  max: number
  step: number
  onChange: (value: number) => void
  disabled?: boolean
}

function SliderWithInput({ value, min, max, step, onChange, disabled = false }: SliderWithInputProps) {
  const { t } = useTranslation()

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue = Number(e.target.value)
    // Validate range
    if (inputValue >= min && inputValue <= max) {
      onChange(inputValue)
    }
  }

  const handleInputBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const inputValue = Number(e.target.value)
    // Clamp value to valid range on blur
    if (inputValue < min) {
      onChange(min)
    } else if (inputValue > max) {
      onChange(max)
    }
  }

  return (
    <Stack direction="row" spacing={1} alignItems="center" sx={{ width: '100%' }}>
      <Slider
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(_, newValue) => onChange(newValue as number)}
        disabled={disabled}
        sx={{ flex: 1 }}
      />
      <Stack direction="row" spacing={0.5} alignItems="center" sx={{ flexShrink: 0 }}>
        <TextField
          type="number"
          value={value}
          onChange={handleInputChange}
          onBlur={handleInputBlur}
          disabled={disabled}
          inputProps={{ min, max, style: { textAlign: 'center' } }}
          size="small"
          sx={{
            width: 48,
            '& .MuiOutlinedInput-root': {
              height: 28,
              '& input': {
                padding: '4px 6px',
                fontSize: '0.75rem',
                color: 'text.primary',
              },
            },
          }}
        />
        <Typography variant="caption" color="text.secondary" sx={{ whiteSpace: 'nowrap' }}>
          {t('settings.dataRetentionSettings.days')}
        </Typography>
      </Stack>
    </Stack>
  )
}

interface ConfirmationDialogProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmText: string
  isDestructive?: boolean
}

function ConfirmationDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText,
  isDestructive = false
}: ConfirmationDialogProps) {
  const { t } = useTranslation()

  if (!isOpen) return null

  return (
    <Box
      sx={{
        position: 'fixed',
        inset: 0,
        bgcolor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 50
      }}
    >
      <Card sx={{ maxWidth: 448, width: '100%', m: 2, p: 3 }}>
        <Typography variant="h6" fontWeight={600} sx={{ mb: 1.5, color: 'primary.main' }}>
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          {message}
        </Typography>

        <Stack direction="row" spacing={1.5} justifyContent="flex-end">
          <Button
            onClick={onClose}
            variant="outline"
            size="sm"
            sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
          >
            {t('common.cancel')}
          </Button>
          <Button
            onClick={onConfirm}
            variant={isDestructive ? 'destructive' : 'primary'}
            size="sm"
            sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
          >
            {confirmText}
          </Button>
        </Stack>
      </Card>
    </Box>
  )
}

export function DataRetentionSettings() {
  const { t } = useTranslation()
  const {
    settings,
    isLoading,
    error,
    isOperationInProgress,
    previewResult,
    isBackendConnected,
    updateRetentionSettings,
    previewCleanup,
    performCleanup,
    limits
  } = useRetentionSettings()

  const [showPreviewDialog, setShowPreviewDialog] = useState(false)
  const [showCleanupConfirm, setShowCleanupConfirm] = useState(false)
  const [confirmationText, setConfirmationText] = useState('')
  const [validationErrors, setValidationErrors] = useState<string[]>([])
  const [isDangerousOperation, setIsDangerousOperation] = useState(false)
  const [cleanupSuccess, setCleanupSuccess] = useState<string | null>(null)
  const [cleanupError, setCleanupError] = useState<string | null>(null)

  // Enhanced validation with security checks
  useEffect(() => {
    if (!settings) return

    const errors: string[] = []
    let isDangerous = false

    // Check for potentially dangerous configurations
    if (settings.log_retention < 14) {
      errors.push(t('settings.dataRetentionSettings.validationErrors.logRetentionLow'))
      isDangerous = true
    }

    if (settings.data_retention < 90) {
      errors.push(t('settings.dataRetentionSettings.validationErrors.otherDataRetentionLow'))
      isDangerous = true
    }

    setValidationErrors(errors)
    setIsDangerousOperation(isDangerous)
  }, [settings])

  if (isLoading) {
    return (
      <Box>
        <Typography variant="body2" color="text.secondary">
          {t('settings.dataRetentionSettings.loadingSettings')}
        </Typography>
      </Box>
    )
  }

  if (!settings) {
    return (
      <Box>
        <Typography variant="body2" color="error.main">
          {t('settings.dataRetentionSettings.failedToLoad')}
        </Typography>
      </Box>
    )
  }

  const handlePreviewCleanup = async () => {
    const result = await previewCleanup()
    if (result.success) {
      setShowPreviewDialog(true)
    }
  }

  const handleConfirmCleanup = () => {
    setShowPreviewDialog(false)
    setShowCleanupConfirm(true)
    setConfirmationText('')  // Reset confirmation text
  }

  const handleFinalCleanup = async () => {
    // Validate confirmation text for dangerous operations
    const requiredText = 'DELETE DATA'
    if (isDangerousOperation && confirmationText !== requiredText) {
      return // Don't proceed without proper confirmation
    }

    setShowCleanupConfirm(false)
    setConfirmationText('')
    setCleanupSuccess(null)
    setCleanupError(null)

    // Execute cleanup with CSRF protection
    const result = await performCleanup('logs')

    if (result.success) {
      const totalDeleted = result.deletedCounts
        ? Object.values(result.deletedCounts).reduce((sum, count) => sum + count, 0)
        : 0
      const spaceFreed = result.preview?.estimatedSpaceFreed || '0 MB'
      setCleanupSuccess(
        `Cleanup completed: ${totalDeleted} records deleted, ${spaceFreed} freed`
      )
    } else {
      setCleanupError(result.error || 'Cleanup operation failed')
    }
  }

  return (
    <Box>
      <Stack direction="row" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography sx={{ fontSize: '0.9rem', fontWeight: 600, color: 'primary.main', lineHeight: 1.2 }}>
            {t('settings.dataRetentionSettings.title')}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {t('settings.dataRetentionSettings.description')}
          </Typography>
        </Box>
        <Button
          onClick={handlePreviewCleanup}
          disabled={isOperationInProgress || !isBackendConnected}
          variant="outline"
          size="sm"
          sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
        >
          {isOperationInProgress ? t('settings.dataRetentionSettings.analyzing') : t('settings.dataRetentionSettings.previewCleanup')}
        </Button>
      </Stack>

      {!isBackendConnected && (
        <Alert severity="warning" sx={{ mb: 1.5 }}>
          {t('settings.dataRetentionSettings.backendNotConnected')}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 1.5 }}>
          {error}
        </Alert>
      )}

      {cleanupError && (
        <Alert severity="error" sx={{ mb: 1.5 }}>
          {cleanupError}
        </Alert>
      )}

      {cleanupSuccess && (
        <Alert severity="success" sx={{ mb: 1.5 }}>
          {cleanupSuccess}
        </Alert>
      )}

      {validationErrors.length > 0 && (
        <Box sx={{ mb: 1.5 }}>
          {validationErrors.map((error, index) => (
            <Typography key={index} variant="caption" color="text.secondary">
              {error}
            </Typography>
          ))}
        </Box>
      )}

      <Stack spacing={0}>
        <SettingRow
          label={t('settings.dataRetentionSettings.logRetention')}
          children={
            <Box sx={{ flex: 1, maxWidth: 320 }}>
              <SliderWithInput
                value={settings.log_retention}
                min={limits.LOG_MIN}
                max={limits.LOG_MAX}
                step={1}
                onChange={(value) => updateRetentionSettings({ log_retention: value })}
              />
            </Box>
          }
        />

        <SettingRow
          label={t('settings.dataRetentionSettings.dataRetention')}
          children={
            <Box sx={{ flex: 1, maxWidth: 320 }}>
              <SliderWithInput
                value={settings.data_retention}
                min={limits.DATA_MIN}
                max={limits.DATA_MAX}
                step={1}
                onChange={(value) => updateRetentionSettings({ data_retention: value })}
              />
            </Box>
          }
        />
      </Stack>

      {/* Preview Dialog */}
      <ConfirmationDialog
        isOpen={showPreviewDialog}
        onClose={() => setShowPreviewDialog(false)}
        onConfirm={handleConfirmCleanup}
        title={t('settings.dataRetentionSettings.cleanupPreviewTitle')}
        message={
          previewResult
            ? t('settings.dataRetentionSettings.cleanupPreviewMessage', {
                logEntries: previewResult.logEntriesAffected,
                otherRecords: previewResult.otherDataAffected,
                space: previewResult.estimatedSpaceFreed
              })
            : t('settings.dataRetentionSettings.previewNotAvailable')
        }
        confirmText={t('settings.dataRetentionSettings.continue')}
      />

      {/* Enhanced Final Confirmation Dialog */}
      {showCleanupConfirm && (
        <Box
          sx={{
            position: 'fixed',
            inset: 0,
            bgcolor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 50
          }}
        >
          <Card sx={{ maxWidth: 448, width: '100%', m: 2, p: 3 }}>
            <Typography variant="h6" fontWeight={600} sx={{ mb: 1.5, color: 'error.main' }}>
              {t('settings.dataRetentionSettings.confirmDeletion')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('settings.dataRetentionSettings.deletionWarning')}
            </Typography>

            {isDangerousOperation && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" fontWeight={500} sx={{ mb: 1, color: 'error.dark' }}>
                  {t('settings.dataRetentionSettings.typeToConfirm')}
                </Typography>
                <TextField
                  type="text"
                  value={confirmationText}
                  onChange={(e) => setConfirmationText(e.target.value)}
                  placeholder="DELETE DATA"
                  size="small"
                  fullWidth
                />
              </Box>
            )}

            <Stack direction="row" spacing={1.5} justifyContent="flex-end">
              <Button
                onClick={() => {
                  setShowCleanupConfirm(false)
                  setConfirmationText('')
                }}
                variant="outline"
                size="sm"
                sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
              >
                {t('common.cancel')}
              </Button>
              <Button
                onClick={handleFinalCleanup}
                disabled={isDangerousOperation && confirmationText !== 'DELETE DATA'}
                variant="destructive"
                size="sm"
                sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
              >
                {t('settings.dataRetentionSettings.deleteData')}
              </Button>
            </Stack>
          </Card>
        </Box>
      )}
    </Box>
  )
}