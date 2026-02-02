/**
 * Timezone Dropdown Component
 *
 * A dropdown component for selecting timezones with popular options
 * and regional grouping. Integrates with the settings system.
 * Styled to match the custom Select component.
 */

import { useState } from 'react'
import { Select, MenuItem, ListSubheader, SelectChangeEvent } from '@mui/material'
import { useTimezone } from '@/hooks/useTimezone'

interface TimezoneDropdownProps {
  className?: string
  disabled?: boolean
}

export function TimezoneDropdown({ disabled = false }: TimezoneDropdownProps) {
  const {
    isLoading,
    error,
    currentTimezone,
    timezoneGroups,
    popularTimezones,
    updateTimezone
  } = useTimezone()

  const [isUpdating, setIsUpdating] = useState(false)

  const handleTimezoneChange = async (event: SelectChangeEvent<string>) => {
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

  // Common styles to match the custom Select component
  const selectStyles = {
    height: 32,
    minWidth: 144,
    fontSize: '0.75rem',
    borderRadius: 1,
    bgcolor: 'transparent',
    '& .MuiOutlinedInput-notchedOutline': {
      borderColor: 'rgba(255, 255, 255, 0.23)'
    },
    '&:hover .MuiOutlinedInput-notchedOutline': {
      borderColor: 'rgba(255, 255, 255, 0.4)'
    },
    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
      borderColor: 'primary.main',
      borderWidth: 1
    },
    '& .MuiSelect-select': {
      py: 0.5,
      px: 1
    }
  }

  if (isLoading) {
    return (
      <Select
        disabled
        size="small"
        value=""
        sx={selectStyles}
      >
        <MenuItem value="">Loading...</MenuItem>
      </Select>
    )
  }

  if (error) {
    return (
      <Select
        disabled
        size="small"
        value=""
        sx={selectStyles}
      >
        <MenuItem value="">Error</MenuItem>
      </Select>
    )
  }

  return (
    <Select
      value={currentTimezone}
      onChange={handleTimezoneChange}
      disabled={disabled || isUpdating}
      size="small"
      sx={selectStyles}
      MenuProps={{
        PaperProps: {
          sx: {
            maxHeight: 300,
            '& .MuiMenuItem-root': {
              fontSize: '0.75rem'
            },
            '& .MuiListSubheader-root': {
              fontSize: '0.7rem',
              fontWeight: 600,
              color: 'text.secondary',
              lineHeight: 2.5
            }
          }
        }
      }}
    >
      {/* Popular timezones */}
      {popularTimezones.length > 0 && [
        <ListSubheader key="popular-header">Popular Timezones</ListSubheader>,
        ...popularTimezones.map((timezone) => (
          <MenuItem key={timezone.id} value={timezone.id}>
            {timezone.name} (UTC{timezone.offset >= 0 ? '+' : ''}{Math.floor(timezone.offset / 60)})
          </MenuItem>
        ))
      ]}

      {/* Regional groups */}
      {timezoneGroups.map((group) => [
        <ListSubheader key={`${group.region}-header`}>{group.region}</ListSubheader>,
        ...group.timezones.map((timezone) => (
          <MenuItem key={timezone.id} value={timezone.id}>
            {timezone.name} (UTC{timezone.offset >= 0 ? '+' : ''}{Math.floor(timezone.offset / 60)})
          </MenuItem>
        ))
      ])}
    </Select>
  )
}
