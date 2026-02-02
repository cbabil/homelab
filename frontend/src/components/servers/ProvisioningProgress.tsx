/**
 * Provisioning Progress Component
 *
 * Displays server provisioning progress with visual stepper,
 * decision panels for Docker/Agent prompts, and cancel option.
 */

import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Stack, Typography, Box } from '@mui/material'
import { CheckCircle, XCircle, Circle, MinusCircle } from 'lucide-react'
import { ProvisioningState, ProvisioningStep, ProvisioningStepStatus } from '@/types/server'
import { Button } from '@/components/ui/Button'
import { DockerDecisionPanel } from './DockerDecisionPanel'
import { AgentDecisionPanel } from './AgentDecisionPanel'

export interface ProvisioningProgressProps {
  state: ProvisioningState
  onInstallDocker: () => void
  onSkipDocker: () => void
  onInstallAgent: () => void
  onSkipAgent: () => void
  onRetry: () => void
  onCancel: () => void
  onComplete?: () => void
}

const STEP_LABELS: Record<ProvisioningStep['id'], string> = {
  connection: 'servers.provisioning.testingConnection',
  docker: 'servers.provisioning.checkingDocker',
  agent: 'servers.provisioning.installingAgent',
}

function AnimatedDots() {
  return (
    <Box
      component="span"
      sx={{
        '&::after': {
          content: '"..."',
          animation: 'dots 1.5s steps(4, end) infinite',
          display: 'inline-block',
          width: '1.5em',
          textAlign: 'left',
        },
        '@keyframes dots': {
          '0%': { content: '""' },
          '25%': { content: '"."' },
          '50%': { content: '".."' },
          '75%': { content: '"..."' },
          '100%': { content: '""' },
        },
      }}
    />
  )
}

function StatusIcon({ status }: { status: ProvisioningStepStatus }) {
  const icons: Record<ProvisioningStepStatus, React.ReactNode> = {
    success: <CheckCircle size={20} color="#10b981" />,
    error: <XCircle size={20} color="#ef4444" />,
    skipped: <MinusCircle size={20} color="#6b7280" />,
    active: <Circle size={20} color="#8b5cf6" />,
    pending: <Circle size={20} color="#9ca3af" />,
  }
  return <>{icons[status]}</>
}

function ElapsedTime({ startTime }: { startTime: number }) {
  const { t } = useTranslation()
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => setElapsed(Math.floor((Date.now() - startTime) / 1000)), 1000)
    return () => clearInterval(interval)
  }, [startTime])

  return (
    <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
      {t('time.seconds', { count: elapsed })}
    </Typography>
  )
}

function StepRow({ step, isActive }: { step: ProvisioningStep; isActive: boolean }) {
  const { t } = useTranslation()

  return (
    <Stack direction="row" alignItems="center" spacing={1.5} sx={{ py: 1 }}>
      <StatusIcon status={step.status} />
      <Box sx={{ flex: 1 }}>
        <Stack direction="row" alignItems="center">
          <Typography
            variant="body2"
            fontWeight={isActive ? 600 : 400}
            color={step.status === 'error' ? 'error.main' : 'text.primary'}
          >
            {t(STEP_LABELS[step.id])}{step.status === 'active' && <AnimatedDots />}
          </Typography>
          {step.status === 'active' && <ElapsedTime startTime={Date.now() - (step.duration || 0)} />}
        </Stack>
        {step.error && (
          <Typography variant="caption" color="error.main" sx={{ display: 'block', mt: 0.5 }}>
            {step.error}
          </Typography>
        )}
      </Box>
    </Stack>
  )
}

export function ProvisioningProgress({
  state, onInstallDocker, onSkipDocker, onInstallAgent, onSkipAgent, onRetry, onCancel, onComplete,
}: ProvisioningProgressProps) {
  const { t } = useTranslation()
  const isComplete = state.currentStep === 'complete' && !state.isProvisioning

  return (
    <Stack spacing={2} sx={{ py: 1 }}>
      <Stack spacing={0}>
        {state.steps.map((step) => (
          <StepRow key={step.id} step={step} isActive={state.currentStep === step.id} />
        ))}
      </Stack>

      {state.requiresDecision === 'docker' && (
        <DockerDecisionPanel onInstall={onInstallDocker} onSkip={onSkipDocker} />
      )}
      {state.requiresDecision === 'agent' && (
        <AgentDecisionPanel onInstall={onInstallAgent} onSkip={onSkipAgent} />
      )}

      {state.canRetry && (
        <Button variant="outline" size="xs" onClick={onRetry} fullWidth>
          {t('servers.provisioning.retry')}
        </Button>
      )}
      {isComplete && onComplete && (
        <Button variant="primary" size="xs" onClick={onComplete} fullWidth>
          {t('common.done')}
        </Button>
      )}
      {state.isProvisioning && (
        <Stack direction="row" justifyContent="flex-end">
          <Button variant="ghost" size="xs" onClick={onCancel}>
            {t('common.cancel')}
          </Button>
        </Stack>
      )}
    </Stack>
  )
}
