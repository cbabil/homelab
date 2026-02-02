/**
 * Requirements Section Component
 *
 * Form section for application system requirements.
 */

import { Box, Typography, TextField, Stack, Grid } from '@mui/material'
import { AppRequirements } from '@/types/app'

interface RequirementsSectionProps {
  requirements: AppRequirements
  onChange: (field: string, value: string | string[] | number[]) => void
}

export function RequirementsSection({ requirements, onChange }: RequirementsSectionProps) {
  const handlePortsChange = (value: string) => {
    const ports = value.split(',')
      .map(port => parseInt(port.trim()))
      .filter(port => !isNaN(port))
    onChange('requiredPorts', ports)
  }

  const handleDependenciesChange = (value: string) => {
    const deps = value.split(',').map(dep => dep.trim()).filter(Boolean)
    onChange('dependencies', deps)
  }

  const handleArchitecturesChange = (value: string) => {
    const archs = value.split(',').map(arch => arch.trim()).filter(Boolean)
    onChange('supportedArchitectures', archs)
  }

  return (
    <Stack spacing={0.75} sx={{ borderTop: 1, borderColor: 'divider', pt: 0.75 }}>
      <Typography variant="body2" fontWeight={500} sx={{ mb: 1 }}>System Requirements</Typography>

      <Grid container spacing={1.5}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Typography variant="body2" fontWeight={500} sx={{ mb: 0.5 }}>Min RAM</Typography>
          <TextField
            type="text"
            size="small"
            fullWidth
            value={requirements.minRam || ''}
            onChange={(e) => onChange('minRam', e.target.value)}
            placeholder="512MB, 1GB, 2GB"
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 6 }}>
          <Typography variant="body2" fontWeight={500} sx={{ mb: 0.5 }}>Min Storage</Typography>
          <TextField
            type="text"
            size="small"
            fullWidth
            value={requirements.minStorage || ''}
            onChange={(e) => onChange('minStorage', e.target.value)}
            placeholder="100MB, 1GB, 10GB"
          />
        </Grid>
      </Grid>

      <Grid container spacing={1.25} sx={{ mt: 1.25 }}>
        <Grid size={{ xs: 12, lg: 6 }}>
          <Typography variant="body2" fontWeight={500} sx={{ mb: 0.5 }}>Required Ports</Typography>
          <TextField
            type="text"
            size="small"
            fullWidth
            value={requirements.requiredPorts?.join(', ') || ''}
            onChange={(e) => handlePortsChange(e.target.value)}
            placeholder="80, 443, 8080"
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            Separate ports with commas
          </Typography>
        </Grid>

        <Grid size={{ xs: 12, lg: 6 }}>
          <Typography variant="body2" fontWeight={500} sx={{ mb: 0.5 }}>Supported Architectures</Typography>
          <TextField
            type="text"
            size="small"
            fullWidth
            value={requirements.supportedArchitectures?.join(', ') || ''}
            onChange={(e) => handleArchitecturesChange(e.target.value)}
            placeholder="amd64, arm64, armv7"
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            Separate architectures with commas
          </Typography>
        </Grid>
      </Grid>

      <Box sx={{ mt: 1.25 }}>
        <Typography variant="body2" fontWeight={500} sx={{ mb: 0.5 }}>Dependencies</Typography>
        <TextField
          type="text"
          size="small"
          fullWidth
          value={requirements.dependencies?.join(', ') || ''}
          onChange={(e) => handleDependenciesChange(e.target.value)}
          placeholder="docker, postgresql, redis"
        />
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
          Separate dependencies with commas
        </Typography>
      </Box>
    </Stack>
  )
}