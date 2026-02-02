/**
 * Select Component
 *
 * Dropdown select with label and error states.
 * Uses MUI sx props for styling.
 */

import React, { forwardRef } from 'react'
import { ChevronDown } from 'lucide-react'
import { Box, Stack } from '@mui/material'

export interface SelectOption {
  label: string
  value: string
}

export interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  label?: string
  error?: string
  helperText?: string
  size?: 'sm' | 'md' | 'lg'
  fullWidth?: boolean
  options: SelectOption[]
}

interface SelectSizeStyles {
  height: number
  px: number
  fontSize: string
}

const selectSizes: Record<'sm' | 'md' | 'lg', SelectSizeStyles> = {
  sm: { height: 32, px: 1, fontSize: '0.75rem' },
  md: { height: 40, px: 1.5, fontSize: '0.875rem' },
  lg: { height: 48, px: 2, fontSize: '1rem' }
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({
    className: _className,
    label,
    error,
    helperText,
    size = 'md',
    fullWidth = false,
    options,
    id,
    ...props
  }, ref) => {
    const selectId = id || label?.toLowerCase().replace(/\s+/g, '-')

    return (
      <Stack spacing={0.75} sx={{ width: fullWidth ? '100%' : 'auto' }}>
        {label && (
          <Box
            component="label"
            htmlFor={selectId}
            sx={{ fontSize: '0.875rem', fontWeight: 500, color: 'text.primary' }}
          >
            {label}
          </Box>
        )}

        <Box sx={{ position: 'relative' }}>
          <Box
            component="select"
            ref={ref}
            id={selectId}
            sx={(theme) => {
              const sizeStyles = selectSizes[size]
              return {
                width: '100%',
                appearance: 'none',
                borderRadius: 1,
                border: 1,
                borderColor: error ? 'error.main' : 'rgba(255, 255, 255, 0.23)',
                bgcolor: 'transparent',
                color: 'text.primary',
                pr: 4,
                cursor: 'pointer',
                height: sizeStyles.height,
                px: sizeStyles.px,
                fontSize: sizeStyles.fontSize,
                '&:hover': {
                  borderColor: error ? 'error.main' : 'rgba(255, 255, 255, 0.4)'
                },
                '&:focus': {
                  outline: 'none',
                  borderColor: error ? 'error.main' : 'primary.main',
                  borderWidth: 1
                },
                '&:disabled': {
                  opacity: 0.5,
                  cursor: 'not-allowed'
                },
                '& option': {
                  bgcolor: theme.palette.background.paper,
                  color: theme.palette.text.primary
                }
              }
            }}
            {...props}
          >
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Box>

          <Box
            sx={{
              position: 'absolute',
              right: 12,
              top: '50%',
              transform: 'translateY(-50%)',
              pointerEvents: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <ChevronDown className="w-4 h-4" />
          </Box>
        </Box>

        {(error || helperText) && (
          <Box
            component="p"
            sx={{
              fontSize: '0.75rem',
              color: error ? 'error.main' : 'text.secondary'
            }}
          >
            {error || helperText}
          </Box>
        )}
      </Stack>
    )
  }
)

Select.displayName = 'Select'
