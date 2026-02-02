/**
 * Terms of Service Page
 *
 * Standalone page for Terms of Service, designed to open in popup windows.
 */

import { useTranslation } from 'react-i18next'
import Box from '@mui/material/Box'
import Container from '@mui/material/Container'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Divider from '@mui/material/Divider'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemText from '@mui/material/ListItemText'

export function TermsOfServicePage() {
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
            {t('legal.termsOfService')}
          </Typography>

          <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Typography variant="body2">
              <strong>{t('legal.lastUpdated')}</strong> {new Date().toLocaleDateString()}
            </Typography>

            <Box component="section">
              <Typography variant="h5" fontWeight={600} gutterBottom>
                1. Acceptance of Terms
              </Typography>
              <Typography variant="body2" color="text.secondary">
                By accessing and using the Tomo application, you accept and agree to be bound
                by the terms and provision of this agreement.
              </Typography>
            </Box>

            <Box component="section">
              <Typography variant="h5" fontWeight={600} gutterBottom>
                2. Service Description
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Tomo is a self-hosted application for managing home laboratory infrastructure,
                including server connections, service monitoring, and system administration.
              </Typography>
            </Box>

            <Box component="section">
              <Typography variant="h5" fontWeight={600} gutterBottom>
                3. User Responsibilities
              </Typography>
              <List sx={{ listStyleType: 'disc', pl: 4 }}>
                <ListItem sx={{ display: 'list-item', p: 0, mb: 1 }}>
                  <ListItemText
                    primary="You are responsible for maintaining the confidentiality of your account credentials"
                    primaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
                  />
                </ListItem>
                <ListItem sx={{ display: 'list-item', p: 0, mb: 1 }}>
                  <ListItemText
                    primary="You agree to use the service only for lawful purposes"
                    primaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
                  />
                </ListItem>
                <ListItem sx={{ display: 'list-item', p: 0, mb: 1 }}>
                  <ListItemText
                    primary="You are responsible for securing your tomo infrastructure"
                    primaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
                  />
                </ListItem>
                <ListItem sx={{ display: 'list-item', p: 0, mb: 1 }}>
                  <ListItemText
                    primary="You agree not to attempt to breach security measures"
                    primaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
                  />
                </ListItem>
              </List>
            </Box>

            <Box component="section">
              <Typography variant="h5" fontWeight={600} gutterBottom>
                4. Data and Privacy
              </Typography>
              <Typography variant="body2" color="text.secondary">
                This application is self-hosted on your infrastructure. You maintain full control over
                your data. No data is transmitted to external services without your explicit configuration.
              </Typography>
            </Box>

            <Box component="section">
              <Typography variant="h5" fontWeight={600} gutterBottom>
                5. Security Considerations
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                You acknowledge that this application provides access to your infrastructure and agree to:
              </Typography>
              <List sx={{ listStyleType: 'disc', pl: 4 }}>
                <ListItem sx={{ display: 'list-item', p: 0, mb: 1 }}>
                  <ListItemText
                    primary="Use strong, unique passwords"
                    primaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
                  />
                </ListItem>
                <ListItem sx={{ display: 'list-item', p: 0, mb: 1 }}>
                  <ListItemText
                    primary="Keep the application updated"
                    primaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
                  />
                </ListItem>
                <ListItem sx={{ display: 'list-item', p: 0, mb: 1 }}>
                  <ListItemText
                    primary="Monitor access logs"
                    primaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
                  />
                </ListItem>
                <ListItem sx={{ display: 'list-item', p: 0, mb: 1 }}>
                  <ListItemText
                    primary="Report security issues responsibly"
                    primaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
                  />
                </ListItem>
              </List>
            </Box>

            <Box component="section">
              <Typography variant="h5" fontWeight={600} gutterBottom>
                6. Limitation of Liability
              </Typography>
              <Typography variant="body2" color="text.secondary">
                This software is provided "as is" without warranty. The developers are not liable for
                any damages arising from the use of this application.
              </Typography>
            </Box>

            <Box component="section">
              <Typography variant="h5" fontWeight={600} gutterBottom>
                7. Changes to Terms
              </Typography>
              <Typography variant="body2" color="text.secondary">
                These terms may be updated periodically. Continued use of the application constitutes
                acceptance of updated terms.
              </Typography>
            </Box>

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
          </Box>
        </Paper>
      </Container>
    </Box>
  )
}