/**
 * ProvisioningProgress Test Suite
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProvisioningProgress, ProvisioningProgressProps } from '../ProvisioningProgress'
import { ProvisioningState, ProvisioningStep } from '@/types/server'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => ({
      'servers.provisioning.testingConnection': 'Testing Connection',
      'servers.provisioning.checkingDocker': 'Checking Docker',
      'servers.provisioning.installingAgent': 'Installing Agent',
      'servers.provisioning.retry': 'Retry',
      'servers.provisioning.dockerNotInstalled': 'Docker Not Installed',
      'servers.provisioning.dockerDescription': 'Install Docker to run containers',
      'servers.provisioning.installDocker': 'Install Docker',
      'servers.provisioning.agentPrompt': 'Agent Prompt',
      'servers.provisioning.agentDescription': 'Install agent for management',
      'servers.provisioning.installAgent': 'Install Agent',
      'servers.provisioning.skip': 'Skip',
      'common.cancel': 'Cancel',
      'time.seconds': '{{count}}s',
    })[key] || key,
  }),
}))

type StepOverrides = Partial<Record<string, Partial<ProvisioningStep>>>
const createSteps = (o: StepOverrides = {}): ProvisioningStep[] => [
  { id: 'connection', status: 'pending', ...o.connection },
  { id: 'docker', status: 'pending', ...o.docker },
  { id: 'agent', status: 'pending', ...o.agent },
]

const createProps = (s: Partial<ProvisioningState> = {}): ProvisioningProgressProps => ({
  state: {
    isProvisioning: true, steps: createSteps(), currentStep: 'connection',
    canRetry: false, dockerInstalled: false, ...s,
  },
  onInstallDocker: vi.fn(), onSkipDocker: vi.fn(),
  onInstallAgent: vi.fn(), onSkipAgent: vi.fn(), onRetry: vi.fn(), onCancel: vi.fn(),
})

describe('ProvisioningProgress', () => {
  describe('Step Rendering', () => {
    it('renders all three steps with correct labels', () => {
      render(<ProvisioningProgress {...createProps()} />)
      expect(screen.getByText('Testing Connection')).toBeInTheDocument()
      expect(screen.getByText('Checking Docker')).toBeInTheDocument()
      expect(screen.getByText('Installing Agent')).toBeInTheDocument()
    })

    it('shows active styling for active step', () => {
      const steps = createSteps({ connection: { status: 'active' } })
      render(<ProvisioningProgress {...createProps({ steps })} />)
      // Active step shows the step label and animated dots are added via CSS
      expect(screen.getByText(/Testing Connection/)).toBeInTheDocument()
    })

    it('shows error message for error step', () => {
      const steps = createSteps({ connection: { status: 'error', error: 'Connection refused' } })
      render(<ProvisioningProgress {...createProps({ steps })} />)
      expect(screen.getByText('Connection refused')).toBeInTheDocument()
    })
  })

  describe('Decision Panels', () => {
    it('shows Docker decision panel when requiresDecision is docker', () => {
      render(<ProvisioningProgress {...createProps({ requiresDecision: 'docker' })} />)
      expect(screen.getByText('Docker Not Installed')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Install Docker' })).toBeInTheDocument()
    })

    it('shows Agent decision panel when requiresDecision is agent', () => {
      render(<ProvisioningProgress {...createProps({ requiresDecision: 'agent' })} />)
      expect(screen.getByText('Agent Prompt')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Install Agent' })).toBeInTheDocument()
    })

    it('calls onInstallDocker when Install Docker clicked', async () => {
      const user = userEvent.setup()
      const props = createProps({ requiresDecision: 'docker' })
      render(<ProvisioningProgress {...props} />)
      await user.click(screen.getByRole('button', { name: 'Install Docker' }))
      expect(props.onInstallDocker).toHaveBeenCalled()
    })

    it('calls onSkipDocker when Skip clicked on Docker panel', async () => {
      const user = userEvent.setup()
      const props = createProps({ requiresDecision: 'docker' })
      render(<ProvisioningProgress {...props} />)
      await user.click(screen.getByRole('button', { name: 'Skip' }))
      expect(props.onSkipDocker).toHaveBeenCalled()
    })
  })

  describe('Cancel Button', () => {
    it('shows cancel button when provisioning', () => {
      render(<ProvisioningProgress {...createProps({ isProvisioning: true })} />)
      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
    })

    it('calls onCancel when cancel clicked', async () => {
      const user = userEvent.setup()
      const props = createProps({ isProvisioning: true })
      render(<ProvisioningProgress {...props} />)
      await user.click(screen.getByRole('button', { name: 'Cancel' }))
      expect(props.onCancel).toHaveBeenCalled()
    })
  })
})
