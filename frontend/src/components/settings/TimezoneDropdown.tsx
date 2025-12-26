/**
 * Timezone Dropdown Component
 *
 * A dropdown component for selecting timezones with popular options
 * and regional grouping. Integrates with the settings system.
 */

import { useState } from 'react'
import { useTimezone } from '@/hooks/useTimezone'

interface TimezoneDropdownProps {
  className?: string
  disabled?: boolean
}

export function TimezoneDropdown({ className = '', disabled = false }: TimezoneDropdownProps) {
  const {
    isLoading,
    error,
    currentTimezone,
    timezoneGroups,
    popularTimezones,
    updateTimezone,
    getTimezoneById
  } = useTimezone()

  const [isUpdating, setIsUpdating] = useState(false)

  const handleTimezoneChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
    const newTimezone = event.target.value
    if (newTimezone === currentTimezone) return

    try {
      setIsUpdating(true)
      await updateTimezone(newTimezone)
    } catch (err) {
      console.error('Failed to update timezone:', err)
    } finally {
      setIsUpdating(false)
    }
  }


  if (isLoading) {
    return (
      <select
        disabled
        className={`px-2 py-1 border border-input rounded text-sm bg-background min-w-48 ${className}`}
      >
        <option>Loading timezones...</option>
      </select>
    )
  }

  if (error) {
    return (
      <select
        disabled
        className={`px-2 py-1 border border-input rounded text-sm bg-background min-w-48 ${className}`}
      >
        <option>Error loading timezones</option>
      </select>
    )
  }

  return (
    <select
      value={currentTimezone}
      onChange={handleTimezoneChange}
      disabled={disabled || isUpdating}
      className={`px-2 py-1 border border-input rounded text-sm bg-background min-w-48 ${className}`}
    >
      {/* Popular timezones */}
      {popularTimezones.length > 0 && (
        <optgroup label="Popular Timezones">
          {popularTimezones.map((timezone) => (
            <option key={timezone.id} value={timezone.id}>
              {timezone.name} (UTC{timezone.offset >= 0 ? '+' : ''}{Math.floor(timezone.offset / 60)})
            </option>
          ))}
        </optgroup>
      )}

      {/* Regional groups */}
      {timezoneGroups.map((group) => (
        <optgroup key={group.region} label={group.region}>
          {group.timezones.map((timezone) => (
            <option key={timezone.id} value={timezone.id}>
              {timezone.name} (UTC{timezone.offset >= 0 ? '+' : ''}{Math.floor(timezone.offset / 60)})
            </option>
          ))}
        </optgroup>
      ))}
    </select>
  )
}