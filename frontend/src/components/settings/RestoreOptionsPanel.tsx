/**
 * Restore Options Panel Component
 *
 * Checkbox panel for selecting what data to restore from backup.
 */

import { Settings, Server, Package, AlertCircle } from 'lucide-react'
import { Box, Stack, Typography, Checkbox, FormControlLabel, Grid } from '@mui/material'
import type { SxProps, Theme } from '@mui/material'
import { RestoreOptions } from '@/services/tomoBackupService'

const styles: Record<string, SxProps<Theme>> = {
  container: {
    p: 1.5,
    bgcolor: 'action.selected',
    borderRadius: 1,
    border: 1,
    borderStyle: 'dashed',
    borderColor: 'divider'
  },
  title: {
    fontSize: '0.75rem',
    fontWeight: 500,
    mb: 1,
    color: 'text.secondary'
  },
  grid: {
    mb: 1
  },
  label: {
    fontSize: '0.75rem',
    '& .MuiCheckbox-root': {
      padding: 0.5
    }
  },
  icon: {
    width: 12,
    height: 12,
    marginRight: 0.5
  },
  description: {
    fontSize: '0.75rem',
    color: 'text.secondary'
  }
}

interface RestoreOptionsPanelProps {
  options: RestoreOptions
  onChange: (options: RestoreOptions) => void
}

export function RestoreOptionsPanel({ options, onChange }: RestoreOptionsPanelProps) {
  const updateOption = (key: keyof RestoreOptions, value: boolean) => {
    onChange({ ...options, [key]: value })
  }

  return (
    <Box sx={styles.container}>
      <Typography sx={styles.title}>Import Options</Typography>

      <Grid container spacing={1} sx={styles.grid}>
        <Grid size={{ xs: 6 }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={options.includeSettings}
                onChange={(e) => updateOption('includeSettings', e.target.checked)}
                size="small"
              />
            }
            label={
              <Stack direction="row" alignItems="center" spacing={0.5}>
                <Settings style={{ width: 12, height: 12 }} />
                <span>Settings</span>
              </Stack>
            }
            sx={styles.label}
          />
        </Grid>

        <Grid size={{ xs: 6 }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={options.includeServers}
                onChange={(e) => updateOption('includeServers', e.target.checked)}
                size="small"
              />
            }
            label={
              <Stack direction="row" alignItems="center" spacing={0.5}>
                <Server style={{ width: 12, height: 12 }} />
                <span>Servers</span>
              </Stack>
            }
            sx={styles.label}
          />
        </Grid>

        <Grid size={{ xs: 6 }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={options.includeApplications}
                onChange={(e) => updateOption('includeApplications', e.target.checked)}
                size="small"
              />
            }
            label={
              <Stack direction="row" alignItems="center" spacing={0.5}>
                <Package style={{ width: 12, height: 12 }} />
                <span>Apps</span>
              </Stack>
            }
            sx={styles.label}
          />
        </Grid>

        <Grid size={{ xs: 6 }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={options.overwriteExisting}
                onChange={(e) => updateOption('overwriteExisting', e.target.checked)}
                size="small"
              />
            }
            label={
              <Stack direction="row" alignItems="center" spacing={0.5}>
                <AlertCircle style={{ width: 12, height: 12, color: 'var(--mui-palette-warning-main)' }} />
                <span>Overwrite</span>
              </Stack>
            }
            sx={styles.label}
          />
        </Grid>
      </Grid>

      <Typography sx={styles.description}>
        Select what to restore and whether to overwrite existing data
      </Typography>
    </Box>
  )
}
