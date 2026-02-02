/**
 * Button Component (MUI-based)
 *
 * Wraps MUI Button with consistent API for the application.
 * Supports loading states, icons, and standard variants.
 */

import React, { forwardRef } from 'react'
import MuiButton, { ButtonProps as MuiButtonProps } from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Box from '@mui/material/Box'

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive'
type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'icon'

interface ButtonProps extends Omit<MuiButtonProps, 'variant' | 'size' | 'color'> {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  fullWidth?: boolean
}

// Map our variants to MUI variants and colors
const getButtonProps = (variant: ButtonVariant): { muiVariant: MuiButtonProps['variant']; color: MuiButtonProps['color']; sx?: MuiButtonProps['sx'] } => {
  switch (variant) {
    case 'primary':
      // Primary uses contained but our theme makes it outline style
      return { muiVariant: 'contained', color: 'primary' }
    case 'secondary':
      return { muiVariant: 'contained', color: 'secondary' }
    case 'outline':
      return { muiVariant: 'outlined', color: 'inherit' }
    case 'ghost':
      return { muiVariant: 'text', color: 'inherit' }
    case 'destructive':
      return { muiVariant: 'contained', color: 'error' }
    default:
      return { muiVariant: 'contained', color: 'primary' }
  }
}

// Map our sizes to MUI sizes
const getSizeProps = (size: ButtonSize): { muiSize: MuiButtonProps['size']; sx?: MuiButtonProps['sx'] } => {
  switch (size) {
    case 'xs':
      return { muiSize: 'small', sx: { fontSize: '0.75rem', py: 0.25, px: 1 } }
    case 'sm':
      return { muiSize: 'small' }
    case 'md':
      return { muiSize: 'medium' }
    case 'lg':
      return { muiSize: 'large' }
    case 'icon':
      return {
        muiSize: 'small',
        sx: {
          minWidth: 36,
          width: 36,
          height: 36,
          padding: 0,
          borderRadius: '10px',
        }
      }
    default:
      return { muiSize: 'medium' }
  }
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    variant = 'primary',
    size = 'md',
    loading = false,
    leftIcon,
    rightIcon,
    fullWidth = false,
    children,
    disabled,
    sx,
    ...props
  }, ref) => {
    const isDisabled = disabled || loading
    const { muiVariant, color } = getButtonProps(variant)
    const { muiSize, sx: sizeSx } = getSizeProps(size)

    return (
      <MuiButton
        ref={ref}
        variant={muiVariant}
        color={color}
        size={muiSize}
        disabled={isDisabled}
        fullWidth={fullWidth}
        disableRipple
        disableElevation
        sx={[
          {
            transition: 'none',
            '&:focus': { outline: 'none', boxShadow: 'none' },
            '&:focus-visible': { outline: 'none', boxShadow: 'none' }
          },
          ...(sizeSx ? [sizeSx] : []),
          ...(sx ? (Array.isArray(sx) ? sx : [sx]) : []),
        ]}
        {...props}
      >
        {loading ? (
          <CircularProgress
            size={16}
            color="inherit"
            aria-label="Loading"
          />
        ) : (
          <>
            {leftIcon && (
              <Box component="span" sx={{ display: 'flex', flexShrink: 0, mr: 1 }} aria-hidden="true">
                {leftIcon}
              </Box>
            )}
            {children}
            {rightIcon && (
              <Box component="span" sx={{ display: 'flex', flexShrink: 0, ml: 1 }} aria-hidden="true">
                {rightIcon}
              </Box>
            )}
          </>
        )}
      </MuiButton>
    )
  }
)

Button.displayName = 'Button'
