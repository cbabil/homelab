/**
 * Quick Stats Component
 *
 * Compact stats display for the sidebar showing key metrics.
 */

import { memo, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Server, Package, AlertTriangle } from 'lucide-react'
import { Box, Typography, SxProps, Theme } from '@mui/material'
import { NavigationStats } from '@/hooks/useNavigation'

interface StatItemProps {
  to: string
  icon: ReactNode
  value: string
  label: string
  iconColors: { bgcolor: string; color: string }
  containerSx?: SxProps<Theme>
  labelColor?: string
  valueColor?: string
}

const StatItem = memo(({
  to, icon, value, label, iconColors, containerSx, labelColor, valueColor
}: StatItemProps) => (
  <Box
    component={Link}
    to={to}
    sx={{
      display: 'flex',
      alignItems: 'center',
      gap: 1,
      p: 1,
      borderRadius: 1,
      textDecoration: 'none',
      color: 'inherit',
      transition: 'background-color 0.2s',
      '&:hover': { bgcolor: 'action.hover' },
      ...containerSx
    }}
  >
    <Box
      sx={{
        width: 32,
        height: 32,
        borderRadius: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        ...iconColors
      }}
    >
      {icon}
    </Box>
    <Box sx={{ minWidth: 0 }}>
      <Typography variant="body2" fontWeight={500} lineHeight={1} color={valueColor}>
        {value}
      </Typography>
      <Typography
        variant="caption"
        sx={{ fontSize: 10, mt: 0.25, color: labelColor || 'text.secondary' }}
      >
        {label}
      </Typography>
    </Box>
  </Box>
))

StatItem.displayName = 'StatItem'

interface QuickStatsProps {
  stats: NavigationStats
  className?: string
}

const getServerStatusColor = (status: 'success' | 'warning' | 'default') => {
  if (status === 'success') return { bgcolor: 'success.lighter', color: 'success.main' }
  if (status === 'warning') return { bgcolor: 'warning.lighter', color: 'warning.main' }
  return { bgcolor: 'action.hover', color: 'text.secondary' }
}

export const QuickStats = memo(({ stats, className }: QuickStatsProps) => {
  const { t } = useTranslation()
  const serverStatus = stats.totalServers > 0
    ? stats.connectedServers === stats.totalServers ? 'success' : 'warning'
    : 'default'

  return (
    <Box sx={{ py: 1, px: 2, mb: 2 }} className={className}>
      <Typography
        variant="overline"
        sx={{
          fontSize: 10,
          fontWeight: 600,
          color: 'text.secondary',
          letterSpacing: '0.1em',
          mb: 1,
          display: 'block'
        }}
      >
        {t('nav.overview')}
      </Typography>

      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 1 }}>
        <StatItem
          to="/servers"
          icon={<Server style={{ width: 16, height: 16 }} />}
          value={`${stats.connectedServers}/${stats.totalServers}`}
          label={t('nav.servers')}
          iconColors={getServerStatusColor(serverStatus)}
        />

        <StatItem
          to="/applications"
          icon={<Package style={{ width: 16, height: 16 }} />}
          value={`${stats.installedApps}/${stats.totalApps}`}
          label={t('nav.apps')}
          iconColors={{ bgcolor: 'primary.lighter', color: 'primary.main' }}
        />

        {stats.criticalAlerts > 0 && (
          <StatItem
            to="/logs"
            icon={<AlertTriangle style={{ width: 16, height: 16 }} />}
            value={t('nav.alert', { count: stats.criticalAlerts })}
            label={t('nav.needsAttention')}
            iconColors={{ bgcolor: 'error.light', color: 'error.main' }}
            containerSx={{
              gridColumn: 'span 2',
              bgcolor: 'error.lighter',
              '&:hover': { bgcolor: 'error.light' }
            }}
            valueColor="error.main"
            labelColor="error.dark"
          />
        )}
      </Box>
    </Box>
  )
})

QuickStats.displayName = 'QuickStats'
