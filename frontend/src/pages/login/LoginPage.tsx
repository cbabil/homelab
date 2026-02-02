/**
 * Login Page Component
 *
 * Login page with MUI components and form validation.
 * Auth redirect is handled by LoginPageWrapper to avoid re-renders.
 */

import { Link as RouterLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import Box from '@mui/material/Box'
import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'
import Typography from '@mui/material/Typography'
import Link from '@mui/material/Link'
import { LoginForm } from './LoginForm'
import { CopyrightFooter } from '@/components/ui/CopyrightFooter'
import TomoLogo from '../../../../assets/tomo_logo_minimal.png'

export function LoginPage() {
  const { t } = useTranslation()

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
        background: (theme) =>
          theme.palette.mode === 'dark'
            ? 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)'
            : 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
      }}
    >
      <Box sx={{ width: '100%', maxWidth: 420 }}>
        {/* Header */}
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Box
            component="img"
            src={TomoLogo}
            alt="Tomo Logo"
            sx={{
              width: 80,
              height: 80,
              mx: 'auto',
              mb: 2,
            }}
          />
          <Typography variant="h4" fontWeight={700} gutterBottom>
            {t('auth.welcomeBack')}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {t('auth.loginSubtitle')}
          </Typography>
        </Box>

        {/* Login Form Card */}
        <Card elevation={8} sx={{ borderRadius: 3, transition: 'none' }}>
          <CardContent sx={{ p: 4 }}>
            <LoginForm />
          </CardContent>
        </Card>

        {/* Registration Link */}
        <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 3 }}>
          {t('auth.noAccount')}{' '}
          <Link component={RouterLink} to="/register" underline="none" fontWeight={500}>
            {t('auth.createAccount')}
          </Link>
        </Typography>

        {/* Footer */}
        <Box sx={{ mt: 2 }}>
          <CopyrightFooter />
        </Box>
      </Box>
    </Box>
  )
}