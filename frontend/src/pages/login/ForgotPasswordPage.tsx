/**
 * Forgot Password Page Component
 *
 * Guides users through password recovery options.
 * Since this is a tomo application without email infrastructure,
 * it directs users to contact their admin or use CLI.
 */

import React, { useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import Box from '@mui/material/Box'
import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Link from '@mui/material/Link'
import Alert from '@mui/material/Alert'
import Divider from '@mui/material/Divider'
import { ArrowLeft, Terminal, UserCog, Mail } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { CopyrightFooter } from '@/components/ui/CopyrightFooter'
import TomoLogo from '../../../../assets/tomo_logo_minimal.png'

export function ForgotPasswordPage() {
  const { t } = useTranslation()
  const [username, setUsername] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (username.trim()) {
      setSubmitted(true)
    }
  }

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
      <Box sx={{ width: '100%', maxWidth: 480 }}>
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
            {t('auth.resetYourPassword')}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {t('auth.forgotPasswordSubtitle')}
          </Typography>
        </Box>

        {/* Main Card */}
        <Card elevation={8} sx={{ borderRadius: 3 }}>
          <CardContent sx={{ p: 4 }}>
            {!submitted ? (
              <>
                {/* Username Input */}
                <Box component="form" onSubmit={handleSubmit}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {t('auth.enterUsernamePrompt')}
                  </Typography>
                  <TextField
                    fullWidth
                    label={t('auth.username')}
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder={t('auth.enterYourUsername')}
                    sx={{ mb: 2 }}
                  />
                  <Button
                    type="submit"
                    fullWidth
                    variant="primary"
                    size="lg"
                    disabled={!username.trim()}
                  >
                    {t('auth.showRecoveryOptions')}
                  </Button>
                </Box>

                <Divider sx={{ my: 3 }}>
                  <Typography variant="caption" color="text.secondary">
                    {t('auth.or')}
                  </Typography>
                </Divider>

                {/* Quick Info */}
                <Alert severity="info" sx={{ borderRadius: 2 }}>
                  <Typography variant="body2">
                    <strong>{t('auth.tomoTip')}</strong> {t('auth.tomoTipMessage')}
                  </Typography>
                </Alert>
              </>
            ) : (
              <>
                {/* Recovery Options */}
                <Alert severity="success" sx={{ mb: 3, borderRadius: 2 }}>
                  <Typography variant="body2">
                    {t('auth.recoveryOptionsFor')} <strong>{username}</strong>
                  </Typography>
                </Alert>

                {/* Option 1: Contact Admin */}
                <Box sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <UserCog size={20} />
                    <Typography variant="subtitle1" fontWeight={600}>
                      {t('auth.option1Title')}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>
                    {t('auth.option1Description')}
                  </Typography>
                </Box>

                {/* Option 2: CLI Command */}
                <Box sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Terminal size={20} />
                    <Typography variant="subtitle1" fontWeight={600}>
                      {t('auth.option2Title')}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 4, mb: 1 }}>
                    {t('auth.option2Description')}
                  </Typography>
                  <Box
                    sx={{
                      ml: 4,
                      p: 2,
                      bgcolor: (theme) => theme.palette.mode === 'dark' ? '#1e293b' : '#f1f5f9',
                      borderRadius: 2,
                      fontFamily: 'monospace',
                      fontSize: '0.85rem',
                      overflowX: 'auto',
                    }}
                  >
                    tomo user reset-password -u {username} -p &lt;new-password&gt;
                  </Box>
                </Box>

                {/* Option 3: Re-register */}
                <Box sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Mail size={20} />
                    <Typography variant="subtitle1" fontWeight={600}>
                      {t('auth.option3Title')}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>
                    {t('auth.option3Description')}{' '}
                    <Link component={RouterLink} to="/register" underline="hover">
                      {t('auth.createNewAccount')}
                    </Link>
                    . {t('auth.dataNotTransferred')}
                  </Typography>
                </Box>

                <Divider sx={{ my: 3 }} />

                {/* Reset Form Button */}
                <Button
                  variant="outline"
                  fullWidth
                  onClick={() => setSubmitted(false)}
                >
                  {t('auth.tryDifferentUsername')}
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        {/* Back to Login Link */}
        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Link
            component={RouterLink}
            to="/login"
            underline="hover"
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 0.5,
              fontWeight: 500,
            }}
          >
            <ArrowLeft size={16} />
            {t('auth.backToLogin')}
          </Link>
        </Box>

        {/* Footer */}
        <Box sx={{ mt: 2 }}>
          <CopyrightFooter />
        </Box>
      </Box>
    </Box>
  )
}
