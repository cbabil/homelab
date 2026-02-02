/**
 * App Details Panel Header Component
 *
 * Header section with app icon, name, version, and close button.
 */

import { X, Package } from 'lucide-react'
import { Box, IconButton, Typography, Stack, Button } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { InstalledAppInfo } from '@/hooks/useInstalledApps'
import { TabId, TABS } from './appDetailsPanelUtils'

interface AppDetailsPanelHeaderProps {
  app: InstalledAppInfo
  activeTab: TabId
  onTabChange: (tab: TabId) => void
  onClose: () => void
}

export function AppDetailsPanelHeader({
  app,
  activeTab,
  onTabChange,
  onClose
}: AppDetailsPanelHeaderProps) {
  const { t } = useTranslation()

  return (
    <>
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          px: 2,
          py: 1.5,
          borderBottom: 1,
          borderColor: 'divider'
        }}
      >
        <Stack direction="row" spacing={1.5} alignItems="center">
          <Box
            sx={{
              width: 40,
              height: 40,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              overflow: 'hidden'
            }}
          >
            {app.appIcon ? (
              <img
                src={app.appIcon}
                alt={app.appName}
                style={{ width: 32, height: 32, objectFit: 'contain' }}
                onError={(e) => {
                  e.currentTarget.style.display = 'none'
                }}
              />
            ) : (
              <Package size={20} style={{ opacity: 0.5 }} />
            )}
          </Box>
          <Box>
            <Typography variant="subtitle2" fontWeight={600}>
              {app.appName}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              v{app.appVersion}
            </Typography>
          </Box>
        </Stack>
        <IconButton size="small" onClick={onClose} sx={{ width: 32, height: 32 }}>
          <X size={16} />
        </IconButton>
      </Box>

      {/* Tabs */}
      <Stack direction="row" spacing={2} sx={{ px: 2 }}>
        {TABS.map((tab) => (
          <Button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            sx={{
              px: 1.5,
              py: 1,
              minWidth: 'auto',
              fontSize: '0.875rem',
              fontWeight: 500,
              borderBottom: 2,
              borderRadius: 0,
              borderColor: activeTab === tab.id ? 'primary.main' : 'transparent',
              color: activeTab === tab.id ? 'text.primary' : 'text.secondary',
              '&:hover': {
                bgcolor: 'transparent',
                color: 'text.primary'
              }
            }}
          >
            {t(tab.labelKey)}
          </Button>
        ))}
      </Stack>
    </>
  )
}
