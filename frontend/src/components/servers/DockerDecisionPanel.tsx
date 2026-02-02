/**
 * Docker Decision Panel Component (Stub)
 *
 * Prompts user to install or skip Docker during provisioning.
 * TODO: Full implementation in next task.
 */

import { useTranslation } from 'react-i18next'
import { Stack, Typography } from '@mui/material'
import { Container } from 'lucide-react'
import { Button } from '@/components/ui/Button'

export interface DockerDecisionPanelProps {
  onInstall: () => void
  onSkip: () => void
}

export function DockerDecisionPanel({ onInstall, onSkip }: DockerDecisionPanelProps) {
  const { t } = useTranslation()

  return (
    <Stack spacing={2}>
      <Stack direction="row" spacing={1.5} alignItems="center">
        <Container size={20} color="#3b82f6" />
        <Typography variant="subtitle2">{t('servers.provisioning.dockerNotInstalled')}</Typography>
      </Stack>
      <Typography variant="body2" color="text.secondary">
        {t('servers.provisioning.dockerDescription')}
      </Typography>
      <Stack direction="row" spacing={1}>
        <Button variant="ghost" size="xs" onClick={onSkip}>
          {t('servers.provisioning.skip')}
        </Button>
        <Button variant="primary" size="xs" onClick={onInstall}>
          {t('servers.provisioning.installDocker')}
        </Button>
      </Stack>
    </Stack>
  )
}
