/**
 * Audit Filter Controls Component
 *
 * Filter dropdowns for the agent audit table.
 */

import { useTranslation } from 'react-i18next'
import {
  FormControl,
  Select,
  MenuItem,
  Stack,
  IconButton,
  Tooltip,
  SelectChangeEvent
} from '@mui/material'
import { RefreshCw } from 'lucide-react'
import type { AgentAuditFilters } from '@/services/auditMcpClient'
import type { ServerConnection } from '@/types/server'

// Event type options for filtering (matches design spec)
const EVENT_TYPES = [
  'AGENT_INSTALLED',
  'AGENT_REGISTERED',
  'AGENT_CONNECTED',
  'AGENT_DISCONNECTED',
  'AGENT_REVOKED',
  'AGENT_UNINSTALLED',
  'AGENT_UPDATED',
  'AGENT_ERROR'
] as const

// Log level options
const LOG_LEVELS = ['INFO', 'WARNING', 'ERROR'] as const

// Styles for select components
const selectStyles = {
  height: 32,
  minWidth: 140,
  fontSize: '0.75rem',
  borderRadius: 1,
  bgcolor: 'transparent',
  '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255, 255, 255, 0.23)' },
  '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255, 255, 255, 0.4)' },
  '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: 'primary.main', borderWidth: 1 },
  '& .MuiSelect-select': { py: 0.5, px: 1 }
}

const menuProps = { PaperProps: { sx: { '& .MuiMenuItem-root': { fontSize: '0.75rem' } } } }

interface AuditFilterControlsProps {
  filters: AgentAuditFilters
  onFilterChange: (filters: AgentAuditFilters) => void
  onRefresh: () => Promise<void>
  isLoading: boolean
  servers: ServerConnection[]
}

export function AuditFilterControls({
  filters,
  onFilterChange,
  onRefresh,
  isLoading,
  servers
}: AuditFilterControlsProps) {
  const { t } = useTranslation()

  const handleServerChange = (e: SelectChangeEvent) => {
    onFilterChange({ ...filters, serverId: e.target.value || undefined })
  }

  const handleEventTypeChange = (e: SelectChangeEvent) => {
    onFilterChange({ ...filters, eventType: e.target.value || undefined })
  }

  const handleLevelChange = (e: SelectChangeEvent) => {
    onFilterChange({ ...filters, level: e.target.value || undefined })
  }

  const handleSuccessChange = (e: SelectChangeEvent) => {
    const value = e.target.value
    onFilterChange({
      ...filters,
      successOnly: value === 'success' ? true : value === 'failed' ? false : undefined
    })
  }

  const successValue = filters.successOnly === true ? 'success' : filters.successOnly === false ? 'failed' : ''

  return (
    <Stack direction="row" spacing={1.5} alignItems="center" flexWrap="wrap" sx={{ mb: 2 }}>
      <FormControl size="small">
        <Select value={filters.serverId || ''} onChange={handleServerChange} displayEmpty sx={selectStyles} MenuProps={menuProps} data-testid="filter-server">
          <MenuItem value="">{t('audit.filters.allServers')}</MenuItem>
          {servers.map((server) => (
            <MenuItem key={server.id} value={server.id}>{server.name}</MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl size="small">
        <Select value={filters.eventType || ''} onChange={handleEventTypeChange} displayEmpty sx={selectStyles} MenuProps={menuProps} data-testid="filter-event">
          <MenuItem value="">{t('audit.filters.allEvents')}</MenuItem>
          {EVENT_TYPES.map((type) => (
            <MenuItem key={type} value={type}>{t(`audit.events.${type}`, type)}</MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl size="small">
        <Select value={filters.level || ''} onChange={handleLevelChange} displayEmpty sx={selectStyles} MenuProps={menuProps} data-testid="filter-level">
          <MenuItem value="">{t('audit.filters.allLevels')}</MenuItem>
          {LOG_LEVELS.map((level) => (
            <MenuItem key={level} value={level}>{level}</MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl size="small">
        <Select value={successValue} onChange={handleSuccessChange} displayEmpty sx={selectStyles} MenuProps={menuProps} data-testid="filter-result">
          <MenuItem value="">{t('audit.filters.allResults')}</MenuItem>
          <MenuItem value="success">{t('common.success')}</MenuItem>
          <MenuItem value="failed">{t('common.failed')}</MenuItem>
        </Select>
      </FormControl>

      <Tooltip title={t('common.refresh')}>
        <IconButton onClick={onRefresh} disabled={isLoading} size="small">
          <RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} />
        </IconButton>
      </Tooltip>
    </Stack>
  )
}
