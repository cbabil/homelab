/**
 * Installed Apps Table Component
 *
 * Table view for displaying installed applications with pagination.
 */

import { useState, useMemo, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Package, ExternalLink } from 'lucide-react'
import {
  Chip, Box, Table, TableHead, TableBody, TableRow, TableCell, Typography, Link, Stack
} from '@mui/material'
import { TablePagination } from '@/components/ui/TablePagination'
import { InstalledAppInfo } from '@/hooks/useInstalledApps'
import { useSettingsContext } from '@/providers/SettingsProvider'
import { useDynamicRowCount } from '@/hooks/useDynamicRowCount'
import { formatLogTimestamp } from '@/utils/timezone'
import { SortButton, SortField, SortDirection } from './InstalledAppsTableHeader'
import { ActionButtons } from './InstalledAppsTableActions'
import { DisplayStatus, getStatusChipColor, STATUS_TRANSLATION_KEYS } from './installedAppsUtils'

interface InstalledAppsTableProps {
  apps: InstalledAppInfo[]
  onSelect?: (app: InstalledAppInfo) => void
  selectedId?: string
  onStart?: (app: InstalledAppInfo) => Promise<void>
  onStop?: (app: InstalledAppInfo) => Promise<void>
  onRestart?: (app: InstalledAppInfo) => Promise<void>
  onUninstall?: (app: InstalledAppInfo) => Promise<void>
}

function getAccessUrl(app: InstalledAppInfo): string | null {
  const ports = Object.entries(app.ports)
  if (ports.length === 0 || !app.serverHost) return null
  const [, hostPort] = ports[0]
  return `http://${app.serverHost}:${hostPort}`
}

function sortApps(apps: InstalledAppInfo[], sortField: SortField, sortDirection: SortDirection) {
  return [...apps].sort((a, b) => {
    let comparison = 0
    switch (sortField) {
      case 'appName': comparison = a.appName.localeCompare(b.appName); break
      case 'appVersion': comparison = a.appVersion.localeCompare(b.appVersion); break
      case 'appSource': comparison = a.appSource.localeCompare(b.appSource); break
      case 'appCategory': comparison = a.appCategory.localeCompare(b.appCategory); break
      case 'serverName': comparison = a.serverName.localeCompare(b.serverName); break
      case 'status': comparison = a.status.localeCompare(b.status); break
      case 'installedAt':
        comparison = new Date(a.installedAt).getTime() - new Date(b.installedAt).getTime()
        break
    }
    return sortDirection === 'asc' ? comparison : -comparison
  })
}

interface AppTableRowProps {
  app: InstalledAppInfo
  isSelected: boolean
  displayStatus: DisplayStatus
  userTimezone: string
  onSelect?: (app: InstalledAppInfo) => void
  onStart?: (app: InstalledAppInfo) => Promise<void>
  onStop?: (app: InstalledAppInfo) => Promise<void>
  onRestart?: (app: InstalledAppInfo) => Promise<void>
  onUninstall?: (app: InstalledAppInfo) => Promise<void>
  onUninstallStateChange: (appId: string, isUninstalling: boolean) => void
}

function AppTableRow({
  app, isSelected, displayStatus, userTimezone, onSelect,
  onStart, onStop, onRestart, onUninstall, onUninstallStateChange
}: AppTableRowProps) {
  const { t } = useTranslation()
  const accessUrl = getAccessUrl(app)

  return (
    <TableRow
      sx={{
        borderBottom: 1, borderColor: 'divider', bgcolor: isSelected ? 'action.hover' : 'transparent',
        cursor: 'pointer', transition: 'background-color 0.2s', '&:hover': { bgcolor: 'action.hover' }
      }}
      onClick={() => onSelect?.(app)}
    >
      <TableCell sx={{ px: 2, py: 1.5 }}>
        <Stack direction="row" spacing={1.5} alignItems="center">
          <Box sx={{ width: 24, height: 24, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            {app.appIcon ? (
              <img src={app.appIcon} alt={app.appName} style={{ width: 24, height: 24, objectFit: 'contain' }} />
            ) : (
              <Package size={16} style={{ color: 'var(--mui-palette-text-secondary)' }} />
            )}
          </Box>
          <Typography variant="body2" fontWeight={500} noWrap>{app.appName}</Typography>
        </Stack>
      </TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}><Typography variant="body2" color="text.secondary">{app.appVersion}</Typography></TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}><Typography variant="body2" noWrap>{app.appSource}</Typography></TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}><Typography variant="body2" sx={{ textTransform: 'capitalize' }} noWrap>{app.appCategory}</Typography></TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}><Typography variant="body2" noWrap>{app.serverName}</Typography></TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}>
        <Chip size="small" color={getStatusChipColor(displayStatus)} label={t(STATUS_TRANSLATION_KEYS[displayStatus] || `applications.status.${displayStatus}`)} />
      </TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}>
        {accessUrl ? (
          <Link href={accessUrl} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}
            sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5, fontSize: '0.875rem', textDecoration: 'none', '&:hover': { opacity: 0.8 } }}>
            <ExternalLink size={14} style={{ flexShrink: 0 }} />
            <Box component="span" sx={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{accessUrl.replace('http://', '')}</Box>
          </Link>
        ) : <Typography variant="body2" color="text.secondary">-</Typography>}
      </TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}><Typography variant="body2" color="text.secondary" noWrap>{formatLogTimestamp(app.installedAt, userTimezone)}</Typography></TableCell>
      <TableCell sx={{ px: 2, py: 1.5 }}>
        <ActionButtons app={app} onStart={onStart} onStop={onStop} onRestart={onRestart} onUninstall={onUninstall} onUninstallStateChange={onUninstallStateChange} />
      </TableCell>
    </TableRow>
  )
}

export function InstalledAppsTable({ apps, onSelect, selectedId, onStart, onStop, onRestart, onUninstall }: InstalledAppsTableProps) {
  const { t } = useTranslation()
  const { settings } = useSettingsContext()
  const userTimezone = settings?.ui.timezone || 'UTC'
  const containerRef = useRef<HTMLDivElement>(null)
  const [sortField, setSortField] = useState<SortField>('installedAt')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [currentPage, setCurrentPage] = useState(1)
  const [uninstallingApps, setUninstallingApps] = useState<Set<string>>(new Set())
  const ITEMS_PER_PAGE = useDynamicRowCount(containerRef, { rowHeight: 52 })

  const handleUninstallStateChange = (appId: string, isUninstalling: boolean) => {
    setUninstallingApps(prev => {
      const next = new Set(prev)
      isUninstalling ? next.add(appId) : next.delete(appId)
      return next
    })
  }

  const getDisplayStatus = (app: InstalledAppInfo): DisplayStatus => uninstallingApps.has(app.id) ? 'uninstalling' : app.status

  useEffect(() => { setCurrentPage(1) }, [ITEMS_PER_PAGE])

  const handleSort = (field: SortField) => {
    if (sortField === field) { setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc') }
    else { setSortField(field); setSortDirection('asc') }
    setCurrentPage(1)
  }

  const sortedApps = useMemo(() => sortApps(apps, sortField, sortDirection), [apps, sortField, sortDirection])
  const totalPages = Math.ceil(sortedApps.length / ITEMS_PER_PAGE)
  const paginatedApps = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE
    return sortedApps.slice(start, start + ITEMS_PER_PAGE)
  }, [sortedApps, currentPage, ITEMS_PER_PAGE])

  if (apps.length === 0) {
    return (
      <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Box sx={{ textAlign: 'center', p: 6 }}>
          <Box sx={{ mb: 2, color: 'text.secondary' }}><Package size={64} style={{ opacity: 0.5 }} /></Box>
          <Typography variant="h6" sx={{ mb: 1 }}>{t('applications.noInstalledApps')}</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3, maxWidth: 448, mx: 'auto' }}>{t('applications.noInstalledAppsDescription')}</Typography>
        </Box>
      </Box>
    )
  }

  const headerCellSx = { textAlign: 'left', px: 2, py: 1.5, fontWeight: 500, fontSize: '0.75rem', color: 'text.secondary' }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
      <Box ref={containerRef} sx={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ flex: 1, overflow: 'auto' }}>
          <Table sx={{ tableLayout: 'fixed' }}>
            <TableHead>
              <TableRow sx={{ bgcolor: 'action.hover', borderBottom: 1, borderColor: 'divider', position: 'sticky', top: 0 }}>
                <TableCell sx={{ ...headerCellSx, width: '14%' }}><SortButton field="appName" currentField={sortField} direction={sortDirection} onSort={handleSort}>{t('applications.columns.application')}</SortButton></TableCell>
                <TableCell sx={{ ...headerCellSx, width: '7%' }}><SortButton field="appVersion" currentField={sortField} direction={sortDirection} onSort={handleSort}>{t('applications.columns.version')}</SortButton></TableCell>
                <TableCell sx={{ ...headerCellSx, width: '12%' }}><SortButton field="appSource" currentField={sortField} direction={sortDirection} onSort={handleSort}>{t('applications.columns.marketplace')}</SortButton></TableCell>
                <TableCell sx={{ ...headerCellSx, width: '9%' }}><SortButton field="appCategory" currentField={sortField} direction={sortDirection} onSort={handleSort}>{t('applications.columns.category')}</SortButton></TableCell>
                <TableCell sx={{ ...headerCellSx, width: '10%' }}><SortButton field="serverName" currentField={sortField} direction={sortDirection} onSort={handleSort}>{t('applications.columns.server')}</SortButton></TableCell>
                <TableCell sx={{ ...headerCellSx, width: '8%' }}><SortButton field="status" currentField={sortField} direction={sortDirection} onSort={handleSort}>{t('applications.columns.status')}</SortButton></TableCell>
                <TableCell sx={{ ...headerCellSx, width: '12%' }}>{t('applications.columns.access')}</TableCell>
                <TableCell sx={{ ...headerCellSx, width: '16%' }}><SortButton field="installedAt" currentField={sortField} direction={sortDirection} onSort={handleSort}>{t('applications.columns.installed')}</SortButton></TableCell>
                <TableCell sx={{ ...headerCellSx, textAlign: 'center', width: '12%' }}>{t('applications.columns.actions')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedApps.map((app) => (
                <AppTableRow key={app.id} app={app} isSelected={selectedId === app.id} displayStatus={getDisplayStatus(app)}
                  userTimezone={userTimezone} onSelect={onSelect} onStart={onStart} onStop={onStop} onRestart={onRestart}
                  onUninstall={onUninstall} onUninstallStateChange={handleUninstallStateChange} />
              ))}
            </TableBody>
          </Table>
        </Box>
      </Box>
      <TablePagination currentPage={currentPage} totalPages={totalPages} onPageChange={setCurrentPage} />
    </Box>
  )
}
