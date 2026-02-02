/**
 * Privacy Policy Content Component
 *
 * Content sections for the Privacy Policy page.
 */

import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemText from '@mui/material/ListItemText'
import type { ReactNode } from 'react'

interface PolicyListItemProps {
  text: ReactNode
}

function PolicyListItem({ text }: PolicyListItemProps) {
  return (
    <ListItem sx={{ display: 'list-item', p: 0, mb: 1 }}>
      <ListItemText
        primary={text}
        primaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
      />
    </ListItem>
  )
}

interface PolicySectionProps {
  title: string
  description?: string
  items?: ReactNode[]
  content?: ReactNode
}

function PolicySection({ title, description, items, content }: PolicySectionProps) {
  return (
    <Box component="section">
      <Typography variant="h5" fontWeight={600} gutterBottom>
        {title}
      </Typography>
      {description && (
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {description}
        </Typography>
      )}
      {items && items.length > 0 && (
        <List sx={{ listStyleType: 'disc', pl: 4 }}>
          {items.map((item, index) => (
            <PolicyListItem key={index} text={item} />
          ))}
        </List>
      )}
      {content}
    </Box>
  )
}

const INFORMATION_COLLECTED_ITEMS: ReactNode[] = [
  <><strong>Account Information:</strong> Username, email address, and encrypted passwords</>,
  <><strong>Server Connections:</strong> Hostnames, connection credentials (encrypted)</>,
  <><strong>Application Logs:</strong> Access logs and error logs for troubleshooting</>,
  <><strong>Session Data:</strong> Authentication tokens and session management data</>,
]

const USAGE_ITEMS = [
  'Authenticate and authorize access to your tomo',
  'Manage server connections and infrastructure',
  'Provide monitoring and administrative capabilities',
  'Maintain application security and functionality',
]

const SECURITY_ITEMS = [
  'Passwords are hashed using industry-standard algorithms',
  'Sensitive credentials are encrypted at rest',
  'Session tokens use secure JWT standards',
  'Database access is protected by authentication',
]

const RETENTION_ITEMS = [
  'Delete your account',
  'Remove server connections',
  'Uninstall the application',
]

const RIGHTS_ITEMS = [
  'Access all your stored data',
  'Modify or delete your information',
  'Export your data',
  'Control data sharing preferences',
]

export function PrivacyPolicyContent() {
  return (
    <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Typography variant="body2">
        <strong>Last updated:</strong> {new Date().toLocaleDateString()}
      </Typography>

      <PolicySection
        title="1. Information We Collect"
        description="As a self-hosted application, all data remains on your infrastructure. We collect:"
        items={INFORMATION_COLLECTED_ITEMS}
      />

      <PolicySection
        title="2. How We Use Your Information"
        description="Your information is used solely to:"
        items={USAGE_ITEMS}
      />

      <PolicySection
        title="3. Data Storage and Security"
        description="All data is stored locally on your infrastructure with the following protections:"
        items={SECURITY_ITEMS}
      />

      <PolicySection
        title="4. Data Sharing"
        content={
          <Typography variant="body2" color="text.secondary">
            <strong>We do not share your data with third parties.</strong> This application is entirely
            self-contained and does not transmit data to external services unless explicitly configured
            by you (e.g., monitoring integrations).
          </Typography>
        }
      />

      <PolicySection
        title="5. Data Retention"
        description="You have full control over data retention. Data is kept until you:"
        items={RETENTION_ITEMS}
      />

      <PolicySection
        title="6. Your Rights"
        description="As the data owner, you have the right to:"
        items={RIGHTS_ITEMS}
      />

      <PolicySection
        title="7. Contact Information"
        content={
          <Typography variant="body2" color="text.secondary">
            For privacy-related questions about this self-hosted application,
            consult the application documentation or repository.
          </Typography>
        }
      />
    </Box>
  )
}
