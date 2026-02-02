/**
 * Server Page Header Component
 *
 * Modern header section with title, description, search, and action buttons.
 * Provides clean separation of header functionality from main page logic.
 */

import { useTranslation } from 'react-i18next'
import { Plus, Download, Upload } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { PageHeader } from '@/components/layout/PageHeader'
import { SearchInput } from '@/components/ui/SearchInput'

interface ServerPageHeaderProps {
  onAddServer: () => void
  onExportServers: () => void
  onImportServers: () => void
  searchTerm: string
  onSearchChange: (term: string) => void
}

export function ServerPageHeader({
  onAddServer,
  onExportServers,
  onImportServers,
  searchTerm,
  onSearchChange,
}: ServerPageHeaderProps) {
  const { t } = useTranslation()

  return (
    <PageHeader
      title={t('servers.title')}
      actions={
        <>
          <SearchInput
            value={searchTerm}
            onChange={onSearchChange}
            placeholder={t('servers.searchPlaceholder')}
          />
          <Button
            onClick={onImportServers}
            variant="outline"
            size="sm"
            leftIcon={<Upload style={{ width: 12, height: 12 }} />}
            sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
          >
            {t('servers.import')}
          </Button>
          <Button
            onClick={onExportServers}
            variant="outline"
            size="sm"
            leftIcon={<Download style={{ width: 12, height: 12 }} />}
            sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
          >
            {t('servers.export')}
          </Button>
          <Button
            onClick={onAddServer}
            variant="primary"
            size="sm"
            leftIcon={<Plus style={{ width: 12, height: 12 }} />}
            sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
          >
            {t('common.add')}
          </Button>
        </>
      }
    />
  )
}