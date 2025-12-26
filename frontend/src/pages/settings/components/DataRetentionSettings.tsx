/**
 * Data Retention Settings Component
 *
 * Secure interface for configuring automatic data cleanup policies
 * with multi-step confirmation flows and preview capabilities.
 */

import { useState, useEffect } from 'react'
import { SettingRow, Toggle } from '../components'
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
    <div className="flex items-center space-x-2 w-full">
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        disabled={disabled}
        className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700 disabled:opacity-50"
      />
      <div className="flex items-center space-x-1 flex-shrink-0">
        <input
          type="number"
          min={min}
          max={max}
          value={value}
          onChange={handleInputChange}
          onBlur={handleInputBlur}
          disabled={disabled}
          className="w-14 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-background text-foreground disabled:opacity-50"
        />
        <span className="text-xs text-muted-foreground whitespace-nowrap">Day(s)</span>
      </div>
    </div>
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
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-card rounded-lg border max-w-md w-full m-4 p-6">
        <h3 className="text-lg font-semibold mb-3 text-primary">{title}</h3>
        <p className="text-sm mb-6 text-muted-foreground">{message}</p>

        <div className="flex gap-3 justify-end">
          <Button
            onClick={onClose}
            variant="outline"
            size="md"
          >
            Cancel
          </Button>
          <Button
            onClick={onConfirm}
            variant={isDestructive ? 'destructive' : 'primary'}
            size="md"
          >
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  )
}

export function DataRetentionSettings() {
  const {
    settings,
    isLoading,
    error,
    isOperationInProgress,
    previewResult,
    updateRetentionSettings,
    previewCleanup,
    limits
  } = useRetentionSettings()

  const [showPreviewDialog, setShowPreviewDialog] = useState(false)
  const [showCleanupConfirm, setShowCleanupConfirm] = useState(false)
  const [confirmationText, setConfirmationText] = useState('')
  const [validationErrors, setValidationErrors] = useState<string[]>([])
  const [isDangerousOperation, setIsDangerousOperation] = useState(false)

  // Enhanced validation with security checks
  useEffect(() => {
    if (!settings) return

    const errors: string[] = []
    let isDangerous = false

    // Check for potentially dangerous configurations
    if (settings.logRetentionDays < 14) {
      errors.push('Log retention below 14 days may affect debugging capabilities')
      isDangerous = true
    }

    if (settings.otherDataRetentionDays < 90) {
      errors.push('Very short retention periods may cause data loss')
      isDangerous = true
    }

    if (settings.autoCleanupEnabled && (settings.logRetentionDays < 30)) {
      errors.push('Auto-cleanup with short retention periods requires extra caution')
      isDangerous = true
    }

    setValidationErrors(errors)
    setIsDangerousOperation(isDangerous)
  }, [settings])

  if (isLoading) {
    return (
      <div className="bg-card rounded-lg border p-6">
        <p className="text-sm text-muted-foreground">Loading retention settings...</p>
      </div>
    )
  }

  if (!settings) {
    return (
      <div className="bg-card rounded-lg border p-6">
        <p className="text-sm text-red-600">Failed to load retention settings</p>
      </div>
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

  const handleFinalCleanup = () => {
    // Validate confirmation text for dangerous operations
    const requiredText = 'DELETE DATA'
    if (isDangerousOperation && confirmationText !== requiredText) {
      return // Don't proceed without proper confirmation
    }

    setShowCleanupConfirm(false)
    setConfirmationText('')
    // TODO: Implement actual cleanup execution with CSRF protection
    console.log('Cleanup confirmed - would execute deletion with security checks')
  }

  return (
    <div className="bg-card rounded-lg border p-3">
      <h4 className="text-sm font-semibold mb-3 text-primary">Data Retention</h4>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-3">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {validationErrors.length > 0 && (
        <div className={`border rounded-lg p-3 mb-3 ${
          isDangerousOperation
            ? 'bg-orange-50 border-orange-200'
            : 'bg-yellow-50 border-yellow-200'
        }`}>
          <div className="text-sm">
            {validationErrors.map((error, index) => (
              <p key={index} className={
                isDangerousOperation ? 'text-orange-700' : 'text-yellow-700'
              }>{error}</p>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-0">
        <SettingRow
          label="Auto-cleanup"
          children={
            <Toggle
              checked={settings.autoCleanupEnabled}
              onChange={(enabled) => updateRetentionSettings({ autoCleanupEnabled: enabled })}
            />
          }
        />

        <SettingRow
          label="Log retention"
          children={
            <div className="flex-1 max-w-xs">
              <SliderWithInput
                value={settings.logRetentionDays}
                min={limits.LOG_MIN_DAYS}
                max={limits.LOG_MAX_DAYS}
                step={1}
                onChange={(value) => updateRetentionSettings({ logRetentionDays: value })}
              />
            </div>
          }
        />

        <SettingRow
          label="Other data retention"
          children={
            <div className="flex-1 max-w-xs">
              <SliderWithInput
                value={settings.otherDataRetentionDays}
                min={limits.OTHER_DATA_MIN_DAYS}
                max={limits.OTHER_DATA_MAX_DAYS}
                step={1}
                onChange={(value) => updateRetentionSettings({ otherDataRetentionDays: value })}
              />
            </div>
          }
        />

        <div className="pt-3 border-t">
          <Button
            onClick={handlePreviewCleanup}
            disabled={isOperationInProgress}
            variant="outline"
            size="sm"
          >
            {isOperationInProgress ? 'Analyzing...' : 'Preview Cleanup'}
          </Button>
        </div>
      </div>

      {/* Preview Dialog */}
      <ConfirmationDialog
        isOpen={showPreviewDialog}
        onClose={() => setShowPreviewDialog(false)}
        onConfirm={handleConfirmCleanup}
        title="Cleanup Preview"
        message={
          previewResult
            ? `This will delete ${previewResult.logEntriesAffected} log entries and ${previewResult.otherDataAffected} other records, freeing approximately ${previewResult.estimatedSpaceFreed} of storage space.`
            : 'Preview data not available'
        }
        confirmText="Continue"
      />

      {/* Enhanced Final Confirmation Dialog */}
      {showCleanupConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-card rounded-lg border max-w-md w-full m-4 p-6">
            <h3 className="text-lg font-semibold mb-3 text-red-600">
              Confirm Data Deletion
            </h3>
            <p className="text-sm mb-4 text-muted-foreground">
              This action will permanently delete data and cannot be undone.
            </p>

            {isDangerousOperation && (
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2 text-red-700">
                  Type "DELETE DATA" to confirm:
                </label>
                <input
                  type="text"
                  value={confirmationText}
                  onChange={(e) => setConfirmationText(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="DELETE DATA"
                />
              </div>
            )}

            <div className="flex gap-3 justify-end">
              <Button
                onClick={() => {
                  setShowCleanupConfirm(false)
                  setConfirmationText('')
                }}
                variant="outline"
                size="md"
              >
                Cancel
              </Button>
              <Button
                onClick={handleFinalCleanup}
                disabled={isDangerousOperation && confirmationText !== 'DELETE DATA'}
                variant="destructive"
                size="md"
              >
                Delete Data
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}