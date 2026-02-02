/**
 * Input Component
 *
 * Form input with label, error states, and various sizes.
 * Uses MUI sx props for styling.
 */

import React, { forwardRef } from 'react'
import { Box, Stack } from '@mui/material'

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string
  error?: string
  helperText?: string
  size?: 'sm' | 'md' | 'lg'
  fullWidth?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

interface InputSizeStyles {
  height: number
  px: number
  fontSize: string
}

const inputSizes: Record<'sm' | 'md' | 'lg', InputSizeStyles> = {
  sm: { height: 32, px: 1, fontSize: '0.75rem' },
  md: { height: 40, px: 1.5, fontSize: '0.875rem' },
  lg: { height: 48, px: 2, fontSize: '1rem' }
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({
    className: _className,
    label,
    error,
    helperText,
    size = 'md',
    fullWidth = false,
    leftIcon,
    rightIcon,
    id,
    ...props
  }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')

    return (
      <Stack spacing={0.75} sx={{ width: fullWidth ? '100%' : 'auto' }}>
        {label && (
          <Box
            component="label"
            htmlFor={inputId}
            sx={{ fontSize: '0.875rem', fontWeight: 500, color: 'text.primary' }}
          >
            {label}
          </Box>
        )}

        <Box sx={{ position: 'relative' }}>
          {leftIcon && (
            <Box
              sx={{
                position: 'absolute',
                left: 12,
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'text.secondary'
              }}
            >
              {leftIcon}
            </Box>
          )}

          <Box
            component="input"
            ref={ref}
            id={inputId}
            aria-invalid={!!error}
            aria-describedby={
              error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined
            }
            aria-required={props.required}
            sx={(theme) => {
              const sizeStyles = inputSizes[size]
              return {
                width: '100%',
                borderRadius: 2,
                border: 1,
                borderColor: error ? 'error.main' : 'divider',
                bgcolor: 'background.default',
                color: 'text.primary',
                height: sizeStyles.height,
                px: sizeStyles.px,
                fontSize: sizeStyles.fontSize,
                pl: leftIcon ? 5 : sizeStyles.px,
                pr: rightIcon ? 5 : sizeStyles.px,
                '&::placeholder': {
                  color: 'text.secondary'
                },
                '&:focus-visible': {
                  outline: 'none',
                  boxShadow: error
                    ? `0 0 0 2px ${theme.palette.error.main}33`
                    : `0 0 0 2px ${theme.palette.primary.main}33`,
                  borderColor: error ? 'error.main' : 'primary.main'
                },
                '&:disabled': {
                  opacity: 0.5,
                  cursor: 'not-allowed'
                }
              }
            }}
            {...props}
          />

          {rightIcon && (
            <Box
              aria-hidden="true"
              sx={{
                position: 'absolute',
                right: 12,
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'text.secondary'
              }}
            >
              {rightIcon}
            </Box>
          )}
        </Box>

        {error && (
          <Box
            component="p"
            id={`${inputId}-error`}
            role="alert"
            sx={{ fontSize: '0.75rem', color: 'error.main' }}
          >
            {error}
          </Box>
        )}

        {!error && helperText && (
          <Box
            component="p"
            id={`${inputId}-helper`}
            sx={{ fontSize: '0.75rem', color: 'text.secondary' }}
          >
            {helperText}
          </Box>
        )}
      </Stack>
    )
  }
)

Input.displayName = 'Input'

// Textarea variant
export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  helperText?: string
  fullWidth?: boolean
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({
    className: _className,
    label,
    error,
    helperText,
    fullWidth = false,
    id,
    ...props
  }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')

    return (
      <Stack spacing={0.75} sx={{ width: fullWidth ? '100%' : 'auto' }}>
        {label && (
          <Box
            component="label"
            htmlFor={inputId}
            sx={{ fontSize: '0.875rem', fontWeight: 500, color: 'text.primary' }}
          >
            {label}
          </Box>
        )}

        <Box
          component="textarea"
          ref={ref}
          id={inputId}
          sx={(theme) => ({
            width: '100%',
            borderRadius: 2,
            border: 1,
            borderColor: error ? 'error.main' : 'divider',
            bgcolor: 'background.default',
            color: 'text.primary',
            px: 1.5,
            py: 1,
            fontSize: '0.875rem',
            '&::placeholder': {
              color: 'text.secondary'
            },
            '&:focus': {
              outline: 'none',
              boxShadow: error
                ? `0 0 0 2px ${theme.palette.error.main}33`
                : `0 0 0 2px ${theme.palette.primary.main}33`,
              borderColor: error ? 'error.main' : 'primary.main'
            },
            '&:disabled': {
              opacity: 0.5,
              cursor: 'not-allowed'
            },
            resize: 'none'
          })}
          {...props}
        />

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

Textarea.displayName = 'Textarea'
