# Task 07: Update Password Strength Indicator

## Overview

Update the `PasswordStrengthIndicator` component to support dual-mode display for NIST compliance and legacy mode.

## File to Modify

`frontend/src/components/auth/PasswordStrengthIndicator.tsx`

## Requirements

1. Support NIST mode (length-based strength)
2. Support legacy mode (complexity-based strength)
3. Show appropriate checklist for each mode
4. Add passphrase tip for NIST mode

## Current Implementation

The current implementation uses complexity-based requirements:
- 12+ characters
- Uppercase letter
- Lowercase letter
- Number
- Special character

## New Implementation

```tsx
/**
 * Password Strength Indicator Component
 *
 * Visual indicator for password strength during registration.
 * Supports both NIST SP 800-63B-4 mode and legacy complexity mode.
 */

import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import LinearProgress from '@mui/material/LinearProgress'
import { CheckCircle, Cancel, Info } from '@mui/icons-material'
import { PasswordStrength, NISTPasswordStrength } from '@/types/auth'

interface PasswordStrengthIndicatorProps {
  /** Password strength data (legacy mode) */
  strength?: PasswordStrength
  /** NIST strength data (NIST mode) */
  nistStrength?: NISTPasswordStrength
  /** The password being evaluated */
  password: string
  /** Whether to use NIST mode */
  nistMode?: boolean
  /** Minimum length requirement */
  minLength?: number
}

export function PasswordStrengthIndicator({
  strength,
  nistStrength,
  password,
  nistMode = false,
  minLength = 15
}: PasswordStrengthIndicatorProps) {
  // Don't show anything if no password entered
  if (!password) {
    return null
  }

  // Use NIST mode calculations if enabled
  if (nistMode) {
    return <NISTStrengthIndicator password={password} minLength={minLength} strength={nistStrength} />
  }

  // Legacy mode
  if (!strength) return null

  const getStrengthColor = (score: number): string => {
    if (score <= 2) return 'error.main'
    if (score <= 3) return 'warning.main'
    if (score <= 4) return 'info.main'
    return 'success.main'
  }

  const getStrengthText = (score: number): string => {
    if (score <= 2) return 'Weak'
    if (score <= 3) return 'Fair'
    if (score <= 4) return 'Good'
    return 'Strong'
  }

  const getStrengthValue = (score: number): number => {
    return (score / 5) * 100
  }

  const getBarColor = (score: number): 'error' | 'warning' | 'info' | 'success' => {
    if (score <= 2) return 'error'
    if (score <= 3) return 'warning'
    if (score <= 4) return 'info'
    return 'success'
  }

  return (
    <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
      {/* Strength Bar */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box sx={{ flex: 1 }}>
          <LinearProgress
            variant="determinate"
            value={getStrengthValue(strength.score)}
            color={getBarColor(strength.score)}
            sx={{
              height: 8,
              borderRadius: 1,
              bgcolor: 'action.hover',
            }}
          />
        </Box>
        <Typography
          variant="caption"
          fontWeight={500}
          sx={{ color: getStrengthColor(strength.score), minWidth: 50 }}
        >
          {getStrengthText(strength.score)}
        </Typography>
      </Box>

      {/* Requirements Checklist */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        {[
          { key: 'minLength', label: '12+ characters' },
          { key: 'hasUppercase', label: 'Uppercase letter' },
          { key: 'hasLowercase', label: 'Lowercase letter' },
          { key: 'hasNumber', label: 'Number' },
          { key: 'hasSpecialChar', label: 'Special character' }
        ].map(({ key, label }) => {
          const isMet = strength.requirements[key as keyof typeof strength.requirements]
          return (
            <Box key={key} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {isMet ? (
                <CheckCircle sx={{ fontSize: 14, color: 'success.main' }} />
              ) : (
                <Cancel sx={{ fontSize: 14, color: 'text.disabled' }} />
              )}
              <Typography
                variant="caption"
                sx={{
                  color: isMet ? 'success.dark' : 'text.disabled',
                }}
              >
                {label}
              </Typography>
            </Box>
          )
        })}
      </Box>
    </Box>
  )
}

/**
 * NIST Mode Strength Indicator
 *
 * Shows strength based on length and pattern checks per NIST SP 800-63B-4.
 */
function NISTStrengthIndicator({
  password,
  minLength,
  strength
}: {
  password: string
  minLength: number
  strength?: NISTPasswordStrength
}) {
  // Calculate strength based on length (NIST approach)
  const getStrengthFromLength = (length: number): number => {
    if (length < minLength) return 1
    if (length < 20) return 2
    if (length < 25) return 3
    if (length < 30) return 4
    return 5
  }

  // Check for sequential patterns
  const hasSequentialPattern = (pwd: string): boolean => {
    const sequences = ['0123456789', '9876543210', 'abcdefghijklmnopqrstuvwxyz',
                      'zyxwvutsrqponmlkjihgfedcba', 'qwertyuiop', 'asdfghjkl']
    const lower = pwd.toLowerCase()
    for (const seq of sequences) {
      for (let i = 0; i <= seq.length - 4; i++) {
        if (lower.includes(seq.substring(i, i + 4))) return true
      }
    }
    return false
  }

  // Check for repetitive patterns
  const hasRepetitivePattern = (pwd: string): boolean => {
    return /(.)\1{3,}/.test(pwd)
  }

  const score = getStrengthFromLength(password.length)
  const meetsLength = password.length >= minLength
  const noSequential = !hasSequentialPattern(password)
  const noRepetitive = !hasRepetitivePattern(password)
  const notOnBlocklist = strength ? !strength.blocklist?.isBlocked : true

  const getStrengthColor = (s: number): string => {
    if (s <= 1) return 'error.main'
    if (s <= 2) return 'warning.main'
    if (s <= 3) return 'info.main'
    return 'success.main'
  }

  const getStrengthText = (s: number): string => {
    if (s <= 1) return 'Too Short'
    if (s <= 2) return 'Fair'
    if (s <= 3) return 'Good'
    if (s <= 4) return 'Strong'
    return 'Excellent'
  }

  const getBarColor = (s: number): 'error' | 'warning' | 'info' | 'success' => {
    if (s <= 1) return 'error'
    if (s <= 2) return 'warning'
    if (s <= 3) return 'info'
    return 'success'
  }

  const requirements = [
    { key: 'minLength', label: `At least ${minLength} characters`, met: meetsLength },
    { key: 'noSequential', label: 'No sequential patterns (1234, abcd)', met: noSequential },
    { key: 'noRepetitive', label: 'No repetitive characters (aaaa)', met: noRepetitive },
    { key: 'notCommon', label: 'Not a commonly used password', met: notOnBlocklist }
  ]

  const allMet = requirements.every(r => r.met)

  return (
    <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
      {/* Strength Bar */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box sx={{ flex: 1 }}>
          <LinearProgress
            variant="determinate"
            value={(score / 5) * 100}
            color={getBarColor(score)}
            sx={{
              height: 8,
              borderRadius: 1,
              bgcolor: 'action.hover',
            }}
          />
        </Box>
        <Typography
          variant="caption"
          fontWeight={500}
          sx={{ color: getStrengthColor(score), minWidth: 60 }}
        >
          {getStrengthText(score)}
        </Typography>
      </Box>

      {/* NIST Requirements Checklist */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        {requirements.map(({ key, label, met }) => (
          <Box key={key} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {met ? (
              <CheckCircle sx={{ fontSize: 14, color: 'success.main' }} />
            ) : (
              <Cancel sx={{ fontSize: 14, color: 'text.disabled' }} />
            )}
            <Typography
              variant="caption"
              sx={{
                color: met ? 'success.dark' : 'text.disabled',
              }}
            >
              {label}
            </Typography>
          </Box>
        ))}
      </Box>

      {/* Passphrase Tip */}
      {allMet && password.length >= minLength && password.length < 25 && (
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5, mt: 0.5 }}>
          <Info sx={{ fontSize: 14, color: 'info.main', mt: 0.25 }} />
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            Tip: Use a passphrase like "correct-horse-battery-staple" for even better security
          </Typography>
        </Box>
      )}
    </Box>
  )
}
```

## Update Types

Add to `frontend/src/types/auth.ts`:

```typescript
export interface NISTPasswordStrength {
  /** Score from 1-5 based on length */
  score: number
  /** Whether password is valid per NIST rules */
  isValid: boolean
  /** Feedback messages */
  feedback: string[]
  /** Blocklist check result */
  blocklist?: {
    isBlocked: boolean
    reason?: string
  }
}
```

## Dependencies

- Task 09: i18n labels for checklist items

## Acceptance Criteria

- [ ] Component accepts `nistMode` prop
- [ ] NIST mode shows length-based strength (not complexity)
- [ ] NIST mode checklist: min length, no sequential, no repetitive, not common
- [ ] Legacy mode unchanged (complexity checklist)
- [ ] Passphrase tip shown when requirements met but could be longer
- [ ] Accessible with proper aria attributes
- [ ] Types updated for NIST strength
