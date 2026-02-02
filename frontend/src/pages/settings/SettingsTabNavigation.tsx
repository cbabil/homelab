/**
 * Settings Tab Navigation Component
 *
 * Tab navigation for switching between different settings sections.
 * Uses the same styling pattern as the TabNavigation component.
 */

import { useTranslation } from 'react-i18next'
import { Server, Monitor, Shield, Bell, Cog } from 'lucide-react'
import { ToggleButtonGroup, ToggleButton } from '@mui/material'
import type { Tab } from './types'

interface SettingsTabNavigationProps {
  activeTab: string
  onTabChange: (tabId: string) => void
}

export function SettingsTabNavigation({ activeTab, onTabChange }: SettingsTabNavigationProps) {
  const { t } = useTranslation()

  const tabs: Tab[] = [
    {
      id: 'general',
      label: t('settings.general'),
      icon: Monitor
    },
    {
      id: 'system',
      label: t('settings.system'),
      icon: Cog
    },
    {
      id: 'security',
      label: t('settings.security'),
      icon: Shield
    },
    {
      id: 'notifications',
      label: t('settings.notifications'),
      icon: Bell
    },
    {
      id: 'servers',
      label: t('settings.servers'),
      icon: Server
    }
  ]

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
          </ToggleButton>
        )
      })}
    </ToggleButtonGroup>
  )
}
