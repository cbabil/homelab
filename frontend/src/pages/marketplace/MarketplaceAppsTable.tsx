/**
 * Marketplace Apps Table Component
 *
 * Table view for displaying marketplace applications using DataTable.
 */

import { useTranslation } from 'react-i18next'
import { Package, Download } from 'lucide-react'
import { Box, Typography, IconButton } from '@mui/material'
import { DataTable, ColumnDef } from '@/components/ui/DataTable'
import type { MarketplaceApp } from '@/types/marketplace'

interface MarketplaceAppsTableProps {
  apps: MarketplaceApp[]
  onDeploy?: (app: MarketplaceApp) => void
  repoMap: Map<string, string>
}

export function MarketplaceAppsTable({ apps, onDeploy, repoMap }: MarketplaceAppsTableProps) {
  const { t } = useTranslation()

  const columns: ColumnDef<MarketplaceApp>[] = [
    {
      id: 'icon',
      header: '',
      width: 20,
      sx: { pr: 0, pl: 1 },
      cellSx: { pr: 0, pl: 1 },
      render: (app) => (
        app.icon && (app.icon.startsWith('http') || app.icon.startsWith('data:')) ? (
          <Box
            component="img"
            src={app.icon}
            alt=""
            sx={{ width: 16, height: 16, objectFit: 'contain', display: 'block' }}
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none'
            }}
          />
        ) : (
          <Package style={{ width: 14, height: 14, opacity: 0.5 }} />
        )
      )
    },
    {
      id: 'name',
      header: t('marketplace.columns.name'),
      width: '20%',
      sortable: true,
      sx: { pl: 0.5 },
      cellSx: { pl: 0.5 },
      render: (app) => (
        <Typography variant="body2" fontWeight={500} noWrap>{app.name}</Typography>
      )
    },
    {
      id: 'version',
      header: t('marketplace.columns.version'),
      width: '10%',
      sortable: true,
      render: (app) => (
        <Typography variant="body2" color="text.secondary">v{app.version}</Typography>
      )
    },
    {
      id: 'category',
      header: t('marketplace.columns.category'),
      width: '12%',
      sortable: true,
      render: (app) => (
        <Typography variant="body2" color="primary.main" sx={{ textTransform: 'capitalize' }} noWrap>
          {app.category}
        </Typography>
      )
    },
    {
      id: 'author',
      header: t('marketplace.columns.author'),
      width: '15%',
      sortable: true,
      render: (app) => (
        <Typography variant="body2" color="text.secondary" noWrap>{app.author || '—'}</Typography>
      )
    },
    {
      id: 'source',
      header: t('marketplace.columns.source'),
      width: '15%',
      sortable: true,
      render: (app) => (
        <Typography variant="body2" color="text.secondary" noWrap>
          {repoMap.get(app.repoId) || '—'}
        </Typography>
      )
    },
    {
      id: 'description',
      header: t('marketplace.columns.description'),
      width: '23%',
      cellSx: {
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        maxWidth: 200
      },
      render: (app) => (
        <Typography variant="body2" color="text.secondary" noWrap>
          {app.description || '—'}
        </Typography>
      )
    },
    {
      id: 'actions',
      header: t('common.actions'),
      width: 60,
      align: 'center',
      render: (app) => onDeploy ? (
        <IconButton
          size="small"
          onClick={(e) => {
            e.stopPropagation()
            onDeploy(app)
          }}
          title={t('marketplace.tooltip.deployToServer')}
          sx={{
            p: 0.5,
            color: 'text.secondary',
            '&:hover': { color: 'primary.main' }
          }}
        >
          <Download style={{ width: 14, height: 14 }} />
        </IconButton>
      ) : null
    }
  ]

  const sortFn = (a: MarketplaceApp, b: MarketplaceApp, field: string, direction: 'asc' | 'desc') => {
    let comparison = 0
    switch (field) {
      case 'name':
        comparison = a.name.localeCompare(b.name)
        break
      case 'version':
        comparison = a.version.localeCompare(b.version)
        break
      case 'category':
        comparison = a.category.localeCompare(b.category)
        break
      case 'author':
        comparison = (a.author || '').localeCompare(b.author || '')
        break
      case 'source':
        comparison = (repoMap.get(a.repoId) || '').localeCompare(repoMap.get(b.repoId) || '')
        break
    }
    return direction === 'asc' ? comparison : -comparison
  }

  return (
    <DataTable
      data={apps}
      columns={columns}
      keyExtractor={(app) => app.id}
      emptyTitle={t('marketplace.empty.noApps')}
      emptyMessage={t('marketplace.empty.syncRepo')}
      emptyIcon={Package}
      defaultSortField="name"
      defaultSortDirection="asc"
      sortFn={sortFn}
    />
  )
}
