/**
 * Agent Decision Panel Component (Stub)
 *
 * Prompts user to install or skip Tomo Agent during provisioning.
 * TODO: Full implementation in next task.
 */

import { useTranslation } from 'react-i18next'
import { Stack, Typography } from '@mui/material'
import { Bot } from 'lucide-react'
import { Button } from '@/components/ui/Button'

export interface AgentDecisionPanelProps {
  onInstall: () => void
  onSkip: () => void
}

export function AgentDecisionPanel({ onInstall, onSkip }: AgentDecisionPanelProps) {
  const { t } = useTranslation()

  return (
    <Stack spacing={2}>
      <Stack direction="row" spacing={1.5} alignItems="center">
        <Bot size={20} color="#8b5cf6" />
        <Typography variant="subtitle2">{t('servers.provisioning.agentPrompt')}</Typography>
      </Stack>
      <Typography variant="body2" color="text.secondary">
        {t('servers.provisioning.agentDescription')}
      </Typography>
      <Stack direction="row" spacing={1}>
        <Button variant="ghost" size="xs" onClick={onSkip}>
          {t('servers.provisioning.skip')}
        </Button>
        <Button variant="primary" size="xs" onClick={onInstall}>
          {t('servers.provisioning.installAgent')}
        </Button>
      </Stack>
    </Stack>
  )
}
