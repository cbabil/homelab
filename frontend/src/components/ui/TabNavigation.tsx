/**
 * Tab Navigation Component
 *
 * Reusable tab navigation for switching between different categories.
 * Used by Audit Logs and Access Logs pages.
 */

import { useState, MouseEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Filter, type LucideIcon } from 'lucide-react'
import { ToggleButtonGroup, ToggleButton, Chip, Box, IconButton, Popover, Typography, Badge } from '@mui/material'

export interface Tab {
  id: string
  label: string
  icon: LucideIcon
  count: number
}

export type SeverityLevel = 'all' | 'success' | 'info' | 'warn' | 'error'

interface SeverityOption {
  id: SeverityLevel
  label: string
  color: string
  count: number
}

interface TabNavigationProps {
  activeTab: string
  onTabChange: (tabId: string) => void
  tabs: Tab[]
  // Optional severity filter (only for Audit Logs)
  severity?: SeverityLevel
  onSeverityChange?: (severity: SeverityLevel) => void
  severityOptions?: SeverityOption[]
}

interface TabButtonsProps {
  activeTab: string
  onTabChange: (tabId: string) => void
  tabs: Tab[]
}

function TabButtons({ activeTab, onTabChange, tabs }: TabButtonsProps) {
  return (
    <ToggleButtonGroup
      value={activeTab}
      exclusive
      onChange={(_e, value) => value && onTabChange(value)}
      size="small"
      sx={{ gap: 0.5 }}
    >
      {tabs.map((tab) => {
        const Icon = tab.icon
        const isActive = activeTab === tab.id
        return (
          <ToggleButton
            key={tab.id}
            value={tab.id}
            disableRipple
            disableFocusRipple
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              px: 2,
              py: 1,
              border: 'none !important',
              borderRadius: 1,
              textTransform: 'none',
              transition: 'none !important',
              bgcolor: 'transparent !important',
              color: isActive ? 'text.primary' : 'text.secondary',
              fontWeight: isActive ? 600 : 400
            }}
          >
            <Icon style={{ width: 14, height: 14 }} />
            <span>{tab.label}</span>
            <Chip
              label={tab.count}
              size="small"
              sx={{
                height: 20,
                fontSize: '0.75rem',
                bgcolor: isActive ? 'primary.main' : 'action.selected',
                color: isActive ? 'primary.contrastText' : 'text.secondary',
                transition: 'none',
                '& .MuiChip-label': { px: 1 }
              }}
            />
          </ToggleButton>
        )
      })}
    </ToggleButtonGroup>
  )
}

interface SeverityFilterButtonProps {
  hasActiveFilter: boolean
  onClick: (event: MouseEvent<HTMLButtonElement>) => void
}

function SeverityFilterButton({ hasActiveFilter, onClick }: SeverityFilterButtonProps) {
  return (
    <Badge
      color="primary"
      variant="dot"
      invisible={!hasActiveFilter}
      overlap="circular"
      sx={{ '& .MuiBadge-badge': { right: 4, top: 4 } }}
    >
      <IconButton
        onClick={onClick}
        size="small"
        disableRipple
        sx={{
          p: 0.5,
          color: hasActiveFilter ? 'primary.main' : 'text.secondary',
          '&:hover': { backgroundColor: 'transparent' },
        }}
        aria-label="Filter by severity"
      >
        <Filter className="h-4 w-4" />
      </IconButton>
    </Badge>
  )
}

interface SeverityOptionItemProps {
  option: SeverityOption
  isSelected: boolean
  onSelect: () => void
}

function SeverityOptionItem({ option, isSelected, onSelect }: SeverityOptionItemProps) {
  return (
    <Box
      onClick={onSelect}
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        px: 1.5,
        py: 1,
        borderRadius: 1,
        cursor: 'pointer',
        backgroundColor: isSelected ? 'action.selected' : 'transparent',
        '&:hover': { backgroundColor: isSelected ? 'action.selected' : 'action.hover' },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: option.color }} />
        <Typography variant="body2" fontWeight={isSelected ? 500 : 400}>
          {option.label}
        </Typography>
      </Box>
      <Chip label={option.count} size="small" sx={{ height: 20, fontSize: '0.75rem', minWidth: 28 }} />
    </Box>
  )
}

export function TabNavigation({
  activeTab,
  onTabChange,
  tabs,
  severity = 'all',
  onSeverityChange,
  severityOptions
}: TabNavigationProps) {
  const { t } = useTranslation()
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null)

  const hasActiveFilter = severity !== 'all'
  const open = Boolean(anchorEl)

  const handleFilterClick = (event: MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleFilterClose = () => {
    setAnchorEl(null)
  }

  const handleSeveritySelect = (sev: SeverityLevel) => {
    onSeverityChange?.(sev)
    handleFilterClose()
  }

  // If no severity filter, return just the tabs
  if (!onSeverityChange || !severityOptions) {
    return <TabButtons activeTab={activeTab} onTabChange={onTabChange} tabs={tabs} />
  }

  // With severity filter
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <TabButtons activeTab={activeTab} onTabChange={onTabChange} tabs={tabs} />
      <SeverityFilterButton hasActiveFilter={hasActiveFilter} onClick={handleFilterClick} />
      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleFilterClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
        slotProps={{ paper: { sx: { mt: 1, minWidth: 180 } } }}
      >
        <Box sx={{ p: 1.5 }}>
          <Typography variant="caption" color="text.secondary" sx={{ px: 1, pb: 1, display: 'block' }}>
            {t('logs.filter.filterBySeverity')}
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            {severityOptions.map((option) => (
              <SeverityOptionItem
                key={option.id}
                option={option}
                isSelected={severity === option.id}
                onSelect={() => handleSeveritySelect(option.id)}
              />
            ))}
          </Box>
        </Box>
      </Popover>
    </Box>
  )
}
