/**
 * Application Name Fields Component
 *
 * Form fields for application name, description, and version.
 */

import { Stack, Typography, TextField } from '@mui/material'
import { App } from '@/types/app'

interface ApplicationNameFieldsProps {
  formData: Partial<App>
  onChange: (field: string, value: string | string[]) => void
}

export function ApplicationNameFields({
  formData,
  onChange
}: ApplicationNameFieldsProps) {
  return (
    <Stack spacing={1.5}>
      <div>
        <Typography variant="body2" fontWeight={500} sx={{ mb: 0.5 }}>Application Name</Typography>
        <TextField
          type="text"
          size="small"
          fullWidth
          value={formData.name || ''}
          onChange={(e) => onChange('name', e.target.value)}
          placeholder="Enter application name"
          required
        />
      </div>

      <div>
        <Typography variant="body2" fontWeight={500} sx={{ mb: 0.5 }}>Description</Typography>
        <TextField
          multiline
          rows={2}
          size="small"
          fullWidth
          value={formData.description || ''}
          onChange={(e) => onChange('description', e.target.value)}
          placeholder="Brief description of the application"
          required
        />
      </div>

      <div>
        <Typography variant="body2" fontWeight={500} sx={{ mb: 0.5 }}>Version</Typography>
        <TextField
          type="text"
          size="small"
          fullWidth
          value={formData.version || ''}
          onChange={(e) => onChange('version', e.target.value)}
          placeholder="1.0.0"
          required
        />
      </div>
    </Stack>
  )
}