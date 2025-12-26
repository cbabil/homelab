/**
 * Settings Action Footer Component
 *
 * Footer with action buttons and save status information.
 */

import { useState } from 'react'
import { Check, RotateCcw } from 'lucide-react'
import { useSettingsContext } from '@/providers/SettingsProvider'
import { Button } from '@/components/ui/Button'

export function SettingsActionFooter() {
  const { resetSettings } = useSettingsContext()
  const [isResetting, setIsResetting] = useState(false)
  const [resetSuccess, setResetSuccess] = useState(false)

  const handleResetToDefaults = async () => {
    try {
      setIsResetting(true)
      const result = await resetSettings()

      if (result.success) {
        setResetSuccess(true)
        setTimeout(() => setResetSuccess(false), 2000)
      }
    } catch (error) {
      console.error('Failed to reset settings:', error)
    } finally {
      setIsResetting(false)
    }
  }

  return (
    <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg border flex-shrink-0">
      <div className="flex space-x-2">
        <Button
          onClick={handleResetToDefaults}
          disabled={isResetting}
          variant="outline"
          size="md"
          leftIcon={<RotateCcw className={`w-4 h-4 ${isResetting ? 'animate-spin' : ''}`} />}
        >
          {isResetting ? 'Resetting...' : 'Reset to Defaults'}
        </Button>

        {resetSuccess && (
          <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
            <Check className="w-4 h-4" />
            Settings reset successfully
          </div>
        )}
      </div>

      <div className="text-sm text-muted-foreground flex items-center gap-2">
        <Check className="w-4 h-4 text-green-500" />
        Changes are saved automatically
      </div>
    </div>
  )
}