/**
 * Settings Page Header Component
 *
 * Header section with title, search, and import/export actions.
 */

import { useTranslation } from 'react-i18next'
import { Download, Upload, RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { PageHeader } from '@/components/layout/PageHeader'
import { SearchInput } from '@/components/ui/SearchInput'
import { useSettingsSaving } from './SettingsSavingContext'

interface SettingsHeaderProps {
  searchTerm?: string
  onSearchChange?: (term: string) => void
  onImport?: () => void
  onExport?: () => void
  onReset?: () => void
  isResetting?: boolean
}

export function SettingsHeader({
  searchTerm = '',
  onSearchChange,
  onImport,
  onExport,
  onReset,
  isResetting = false
}: SettingsHeaderProps) {
  const { t } = useTranslation()
  const { isSaving } = useSettingsSaving()

  return (
    <PageHeader
      title={isSaving ? `${t('settings.title')} - Saving...` : t('settings.title')}
      subtitle={t('settings.subtitle')}
      actions={
        <>
          {onSearchChange && (
            <SearchInput
              value={searchTerm}
              onChange={onSearchChange}
              placeholder={t('settings.searchPlaceholder')}
            />
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={onImport}
            leftIcon={<Upload style={{ width: 12, height: 12 }} />}
            sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
          >
            {t('settings.import')}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onExport}
            leftIcon={<Download style={{ width: 12, height: 12 }} />}
            sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
          >
            {t('settings.export')}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onReset}
            disabled={isResetting}
            leftIcon={<RotateCcw style={{ width: 12, height: 12 }} className={isResetting ? 'animate-spin' : ''} />}
            sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
          >
            {t('settings.reset')}
          </Button>
        </>
      }
    />
  )
}
