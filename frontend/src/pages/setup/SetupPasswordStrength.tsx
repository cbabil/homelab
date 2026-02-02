/**
 * Setup Password Strength Indicator Component
 *
 * Displays password strength bars and requirements checklist.
 */

import Box from '@mui/material/Box'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { useTranslation } from 'react-i18next'
import type { PasswordStrength } from '@/types/auth'

interface SetupPasswordStrengthProps {
  passwordStrength: PasswordStrength
}

function getStrengthColor(level: number, score: number): string {
  if (level > score) return 'action.disabled'
  if (score <= 2) return 'error.main'
  if (score <= 3) return 'warning.main'
  if (score <= 4) return 'info.main'
  return 'success.main'
}

export function SetupPasswordStrength({ passwordStrength }: SetupPasswordStrengthProps) {
  const { t } = useTranslation()

  return (
    <Box sx={{ mt: 1 }}>
      <Stack direction="row" spacing={0.5}>
        {[1, 2, 3, 4, 5].map((level) => (
          <Box
            key={level}
            sx={{
              height: 4,
              flex: 1,
              borderRadius: 1,
              bgcolor: getStrengthColor(level, passwordStrength.score),
              transition: 'background-color 0.2s'
            }}
          />
        ))}
      </Stack>
      {passwordStrength.requirements && (
        <Box component="ul" sx={{ mt: 1, pl: 2, listStyle: 'disc', color: 'text.secondary' }}>
          {!passwordStrength.requirements.minLength && (
            <Typography component="li" variant="caption">
              {t('setup.minLength', { count: 12 })}
            </Typography>
          )}
          {!passwordStrength.requirements.hasUppercase && (
            <Typography component="li" variant="caption">
              {t('setup.uppercase')}
            </Typography>
          )}
          {!passwordStrength.requirements.hasLowercase && (
            <Typography component="li" variant="caption">
              {t('setup.lowercase')}
            </Typography>
          )}
          {!passwordStrength.requirements.hasNumber && (
            <Typography component="li" variant="caption">
              {t('setup.number')}
            </Typography>
          )}
          {!passwordStrength.requirements.hasSpecialChar && (
            <Typography component="li" variant="caption">
              {t('setup.special')}
            </Typography>
          )}
        </Box>
      )}
    </Box>
  )
}
