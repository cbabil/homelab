/**
 * Privacy Policy Page
 *
 * Standalone page for Privacy Policy, designed to open in popup windows.
 */

import { useTranslation } from 'react-i18next'
import Box from '@mui/material/Box'
import Container from '@mui/material/Container'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Divider from '@mui/material/Divider'
import { PrivacyPolicyContent } from '@/components/legal/PrivacyPolicyContent'

export function PrivacyPolicyPage() {
  const { t } = useTranslation()
  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: 'background.default',
        p: 4,
      }}
    >
      <Container maxWidth="md">
        <Paper
          elevation={1}
          sx={{
            p: 4,
            borderRadius: 2,
          }}
        >
          <Typography variant="h3" fontWeight={700} gutterBottom>
            {t('legal.privacyPolicy')}
          </Typography>

          <PrivacyPolicyContent />

          <Divider sx={{ my: 3 }} />

          <Box sx={{ textAlign: 'center' }}>
            <Button
              variant="contained"
              onClick={() => window.close()}
              sx={{ px: 4, py: 1 }}
            >
              {t('legal.closeWindow')}
            </Button>
          </Box>
        </Paper>
      </Container>
    </Box>
  )
}