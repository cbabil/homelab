/**
 * DeploymentModal Component Tests
 *
 * Unit tests for the simplified deployment modal UI including server selection
 * and deployment states.
 */

import React from 'react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { DeploymentModal } from '../DeploymentModal'
import { DeploymentStep, DeploymentResult } from '@/hooks/useDeploymentModal'
import { App, AppCategory } from '@/types/app'
import { Package } from 'lucide-react'

// Mock Modal component
vi.mock('@/components/ui/Modal', () => ({
  Modal: ({ isOpen, children, title, footer, onClose }: {
    isOpen: boolean
    children: React.ReactNode
    title?: React.ReactNode
    footer?: React.ReactNode
    onClose: () => void
  }) => (
    isOpen ? (
      <div data-testid="modal" onClick={(e) => e.target === e.currentTarget && onClose()}>
        {title && <div data-testid="modal-title">{title}</div>}
        <div data-testid="modal-content">{children}</div>
        {footer && <div data-testid="modal-footer">{footer}</div>}
      </div>
    ) : null
  )
}))

const mockCategory: AppCategory = {
  id: 'media',
  name: 'Media',
  description: 'Media applications',
  icon: Package,
  color: 'red'
}

const mockApp: App = {
  id: 'plex',
  name: 'Plex',
  description: 'Media server',
  version: '1.0.0',
  category: mockCategory,
  tags: ['media', 'streaming'],
  icon: 'plex.png',
  author: 'Plex Inc',
  license: 'Proprietary',
  requirements: {
    minRam: '2GB',
    requiredPorts: [32400]
  },
  status: 'available',
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z'
}

const mockServers = [
  {
    id: 'srv-1',
    name: 'Docker Server',
    host: '192.168.1.100',
    port: 22,
    username: 'admin',
    auth_type: 'password' as const,
    status: 'connected' as const,
    docker_installed: true,
    created_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 'srv-2',
    name: 'No Docker Server',
    host: '192.168.1.101',
    port: 22,
    username: 'admin',
    auth_type: 'password' as const,
    status: 'connected' as const,
    docker_installed: false,
    created_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 'srv-3',
    name: 'Offline Server',
    host: '192.168.1.102',
    port: 22,
    username: 'admin',
    auth_type: 'password' as const,
    status: 'disconnected' as const,
    docker_installed: true,
    created_at: '2024-01-01T00:00:00Z'
  }
]

describe('DeploymentModal', () => {
  const mockOnClose = vi.fn()
  const mockSetStep = vi.fn()
  const mockSetSelectedServerIds = vi.fn()
  const mockOnDeploy = vi.fn()
  const mockOnCleanup = vi.fn()

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    app: mockApp,
    servers: mockServers,
    step: 'select' as DeploymentStep,
    setStep: mockSetStep,
    selectedServerIds: [] as string[],
    setSelectedServerIds: mockSetSelectedServerIds,
    isDeploying: false,
    error: null as string | null,
    deploymentResult: null as DeploymentResult | null,
    onDeploy: mockOnDeploy,
    onCleanup: mockOnCleanup
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('should not render when isOpen is false', () => {
      render(<DeploymentModal {...defaultProps} isOpen={false} />)
      expect(screen.queryByText(/Deploy Plex/)).not.toBeInTheDocument()
    })

    it('should not render when app is null', () => {
      render(<DeploymentModal {...defaultProps} app={null} />)
      expect(screen.queryByText(/Deploy/)).not.toBeInTheDocument()
    })

    it('should render dialog when isOpen is true with app', () => {
      render(<DeploymentModal {...defaultProps} />)
      expect(screen.getByText('Deploy Plex')).toBeInTheDocument()
    })
  })

  describe('select server step', () => {
    it('should show server selection when step is select', () => {
      render(<DeploymentModal {...defaultProps} />)
      expect(screen.getByText('Select Target Server')).toBeInTheDocument()
    })

    it('should show all servers', () => {
      render(<DeploymentModal {...defaultProps} />)

      expect(screen.getByText('Docker Server')).toBeInTheDocument()
      expect(screen.getByText('No Docker Server')).toBeInTheDocument()
      expect(screen.getByText('Offline Server')).toBeInTheDocument()
    })

    it('should show Ready status for servers with Docker', () => {
      render(<DeploymentModal {...defaultProps} />)
      expect(screen.getByText('Ready')).toBeInTheDocument()
    })

    it('should show No Docker status for servers without Docker', () => {
      render(<DeploymentModal {...defaultProps} />)
      expect(screen.getByText('No Docker')).toBeInTheDocument()
    })

    it('should show Offline status for disconnected servers', () => {
      render(<DeploymentModal {...defaultProps} />)
      expect(screen.getByText('Offline')).toBeInTheDocument()
    })

    it('should disable Deploy button when no server selected', () => {
      render(<DeploymentModal {...defaultProps} />)
      const deployButton = screen.getByRole('button', { name: /deploy/i })
      expect(deployButton).toBeDisabled()
    })

    it('should enable Deploy button when valid server selected', () => {
      render(<DeploymentModal {...defaultProps} selectedServerIds={['srv-1']} />)
      const deployButton = screen.getByRole('button', { name: /deploy/i })
      expect(deployButton).not.toBeDisabled()
    })

    it('should show no servers message when servers is empty', () => {
      render(<DeploymentModal {...defaultProps} servers={[]} />)
      expect(screen.getByText('No Servers Configured')).toBeInTheDocument()
      expect(screen.getByText(/Add a server in the Servers page/)).toBeInTheDocument()
    })

    it('should call onDeploy when Deploy button clicked with valid selection', async () => {
      mockOnDeploy.mockResolvedValue(true)
      const user = userEvent.setup()
      render(<DeploymentModal {...defaultProps} selectedServerIds={['srv-1']} />)

      const deployButton = screen.getByRole('button', { name: /deploy/i })
      await user.click(deployButton)

      expect(mockOnDeploy).toHaveBeenCalled()
    })

    it('should disable Deploy button when isDeploying', () => {
      render(<DeploymentModal {...defaultProps} selectedServerIds={['srv-1']} isDeploying={true} />)

      expect(screen.getByText(/Deploying.../)).toBeInTheDocument()
      const deployButton = screen.getByRole('button', { name: /deploying/i })
      expect(deployButton).toBeDisabled()
    })
  })

  describe('deploying step', () => {
    it('should show deploying UI when step is deploying', () => {
      render(<DeploymentModal {...defaultProps} step="deploying" />)

      expect(screen.getByTestId('dialog-title')).toHaveTextContent(/Deploying.*Plex/)
      expect(screen.getByText('Connecting to server')).toBeInTheDocument()
    })

    it('should show progress steps during deployment', () => {
      render(<DeploymentModal {...defaultProps} step="deploying" />)

      expect(screen.getByText('Pulling Docker image')).toBeInTheDocument()
      expect(screen.getByText('Creating container')).toBeInTheDocument()
      expect(screen.getByText('Starting application')).toBeInTheDocument()
    })
  })

  describe('success step', () => {
    it('should show success UI when step is success', () => {
      render(
        <DeploymentModal
          {...defaultProps}
          step="success"
          deploymentResult={{ success: true, installationId: 'inst-123' }}
        />
      )

      // Shows "Installing..." when in progress
      expect(screen.getByText('Installing')).toBeInTheDocument()
      expect(screen.getByText('inst-123')).toBeInTheDocument()
      // Shows Done button during installation
      expect(screen.getByRole('button', { name: 'Done' })).toBeInTheDocument()
    })

    it('should show completion UI when installation is running', () => {
      render(
        <DeploymentModal
          {...defaultProps}
          step="success"
          selectedServerIds={['srv-1']}
          deploymentResult={{ success: true, installationId: 'inst-123' }}
          installationStatus={{ id: 'inst-123', status: 'running', app_id: 'plex', server_id: 'srv-1' }}
        />
      )

      expect(screen.getByText('Ready to use')).toBeInTheDocument()
      expect(screen.getByText(/Plex is now running and ready to use/)).toBeInTheDocument()
    })

    it('should show Done button', () => {
      render(<DeploymentModal {...defaultProps} step="success" />)
      expect(screen.getByRole('button', { name: 'Done' })).toBeInTheDocument()
    })

    it('should call onClose when Done clicked', async () => {
      const user = userEvent.setup()
      render(<DeploymentModal {...defaultProps} step="success" />)

      await user.click(screen.getByRole('button', { name: 'Done' }))
      expect(mockOnClose).toHaveBeenCalled()
    })
  })

  describe('error step', () => {
    it('should show error UI when step is error', () => {
      render(
        <DeploymentModal
          {...defaultProps}
          step="error"
          error="Container creation failed"
        />
      )

      expect(screen.getByText('Deployment Failed')).toBeInTheDocument()
      expect(screen.getByText('Container creation failed')).toBeInTheDocument()
    })

    it('should show Try Again button in error step', () => {
      render(
        <DeploymentModal
          {...defaultProps}
          step="error"
          error="Container creation failed"
        />
      )
      expect(screen.getByRole('button', { name: 'Try Again' })).toBeInTheDocument()
    })

    it('should call setStep(select) when Try Again clicked', async () => {
      const user = userEvent.setup()
      render(
        <DeploymentModal
          {...defaultProps}
          step="error"
          error="Container creation failed"
        />
      )

      await user.click(screen.getByRole('button', { name: 'Try Again' }))
      expect(mockSetStep).toHaveBeenCalledWith('select')
    })

    it('should show Close button in error step', () => {
      render(
        <DeploymentModal
          {...defaultProps}
          step="error"
          error="Some error"
        />
      )
      expect(screen.getByRole('button', { name: 'Close' })).toBeInTheDocument()
    })

    it('should show Clean Up button when deployment has installationId', () => {
      render(
        <DeploymentModal
          {...defaultProps}
          step="error"
          error="Some error"
          deploymentResult={{ success: false, installationId: 'inst-123' }}
        />
      )
      expect(screen.getByRole('button', { name: 'Clean Up' })).toBeInTheDocument()
    })
  })

  describe('cancel and close', () => {
    it('should call onClose when Cancel clicked', async () => {
      const user = userEvent.setup()
      render(<DeploymentModal {...defaultProps} />)

      await user.click(screen.getByRole('button', { name: 'Cancel' }))
      expect(mockOnClose).toHaveBeenCalled()
    })
  })

  describe('title changes by step', () => {
    it('should show "Deploy" title on select step', () => {
      render(<DeploymentModal {...defaultProps} step="select" />)
      expect(screen.getByTestId('dialog-title')).toHaveTextContent('Deploy Plex')
    })

    it('should show "Deploying" title on deploying step', () => {
      render(<DeploymentModal {...defaultProps} step="deploying" />)
      expect(screen.getByTestId('dialog-title')).toHaveTextContent(/Deploying.*Plex/)
    })

    it('should show "Deploying" title on success step', () => {
      render(<DeploymentModal {...defaultProps} step="success" />)
      expect(screen.getByTestId('dialog-title')).toHaveTextContent(/Deploying.*Plex/)
    })
  })
})
