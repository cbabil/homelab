/**
 * Password Strength Indicator Component
 *
 * Visual indicator for password strength during registration.
 */

import { useMemo } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import LinearProgress from '@mui/material/LinearProgress'
import { CheckCircle, Cancel } from '@mui/icons-material'
import { PasswordStrength } from '@/types/auth'

interface PasswordStrengthIndicatorProps {
  strength: PasswordStrength
  password: string
  minLength?: number
}

interface RequirementItem {
  key: string
  label: string
  isMet: boolean
}

export function PasswordStrengthIndicator({
  strength,
  password,
  minLength = 8
}: PasswordStrengthIndicatorProps) {
  if (!password) {
    return null
  }

  const getBarColor = (score: number): 'error' | 'warning' | 'info' | 'success' => {
    if (score <= 2) return 'error'
    if (score <= 3) return 'warning'
    if (score <= 4) return 'info'
    return 'success'
  }

  const getStrengthText = (score: number): string => {
    if (score <= 2) return 'Weak'
    if (score <= 3) return 'Fair'
    if (score <= 4) return 'Good'
    return 'Strong'
  }

  const requirements = useMemo((): RequirementItem[] => [
    { key: 'minLength', label: `${minLength}+ characters`, isMet: strength.requirements.minLength },
    { key: 'hasUppercase', label: 'Uppercase letter', isMet: strength.requirements.hasUppercase },
    { key: 'hasLowercase', label: 'Lowercase letter', isMet: strength.requirements.hasLowercase },
    { key: 'hasNumber', label: 'Number', isMet: strength.requirements.hasNumber },
    { key: 'hasSpecialChar', label: 'Special character', isMet: strength.requirements.hasSpecialChar }
  ], [strength, minLength])

  return (
    <Box sx={{ mt: 1.5, display: 'flex', flexDirection: 'column', gap: 0.5 }}>
      {/* Strength Bar */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box sx={{ flex: 1 }}>
          <LinearProgress
            variant="determinate"
            value={(strength.score / 5) * 100}
            color={getBarColor(strength.score)}
            sx={{ height: 6, borderRadius: 1, bgcolor: 'action.hover' }}
          />
        </Box>
        <Typography variant="caption" fontWeight={500} sx={{ color: `${getBarColor(strength.score)}.main`, minWidth: 45 }}>
          {getStrengthText(strength.score)}
        </Typography>
      </Box>

      {/* Requirements Checklist */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
        {requirements.map(({ key, label, isMet }) => (
          <Box key={key} sx={{ display: 'flex', alignItems: 'center', gap: 0.25, minWidth: '45%' }}>
            {isMet ? (
              <CheckCircle sx={{ fontSize: 12, color: 'success.main' }} />
            ) : (
              <Cancel sx={{ fontSize: 12, color: 'text.disabled' }} />
            )}
            <Typography variant="caption" sx={{ color: isMet ? 'success.dark' : 'text.disabled', fontSize: '0.7rem' }}>
              {label}
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  )
}
