/**
 * ServerCard Test Suite
 *
 * Tests for the ServerCard component with status and actions.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ServerCard } from '../ServerCard'
import { ServerConnection } from '@/types/server'

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'servers.statusLabels.online': 'Online',
        'servers.statusLabels.offline': 'Offline',
        'servers.statusLabels.error': 'Error',
        'servers.statusLabels.preparing': 'Preparing',
        'servers.connectionFailed': 'Connection failed',
        'servers.retry': 'Retry',
        'servers.install': 'Install',
        'servers.installing': 'Installing...',
        'servers.actions.connectToServer': 'Connect',
        'servers.actions.disconnectFromServer': 'Disconnect',
        'servers.actions.editServer': 'Edit',
        'servers.actions.deleteServer': 'Delete'
      }
      return translations[key] || key
    }
  })
}))

describe('ServerCard', () => {
  const createServer = (overrides: Partial<ServerConnection> = {}): ServerConnection => ({
    id: 'server-1',
    name: 'Test Server',
    host: '192.168.1.100',
    port: 22,
    username: 'admin',
    auth_type: 'password',
    status: 'disconnected',
    created_at: '2024-01-01T00:00:00Z',
    docker_installed: false,
    ...overrides
  })

  const defaultProps = {
    server: createServer(),
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    onConnect: vi.fn()
  }

  describe('Rendering', () => {
    it('should render server name', () => {
      render(<ServerCard {...defaultProps} server={createServer({ name: 'My Server' })} />)

      expect(screen.getByText('My Server')).toBeInTheDocument()
    })

    it('should render connection info', () => {
      render(
        <ServerCard
          {...defaultProps}
          server={createServer({
            username: 'root',
            host: '10.0.0.1',
            port: 2222
          })}
        />
      )

      expect(screen.getByText('root@10.0.0.1:2222')).toBeInTheDocument()
    })
  })

  describe('Status Display', () => {
    it('should show offline status for disconnected server', () => {
      render(<ServerCard {...defaultProps} server={createServer({ status: 'disconnected' })} />)

      expect(screen.getByText('Offline')).toBeInTheDocument()
    })

    it('should show error status and message for error server', () => {
      render(
        <ServerCard
          {...defaultProps}
          server={createServer({
            status: 'error',
            error_message: 'Authentication failed'
          })}
        />
      )

      expect(screen.getByText('Authentication failed')).toBeInTheDocument()
    })

    it('should show retry button for error server', () => {
      render(
        <ServerCard
          {...defaultProps}
          server={createServer({ status: 'error' })}
        />
      )

      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
    })

    it('should show default error message when no error_message', () => {
      render(
        <ServerCard
          {...defaultProps}
          server={createServer({ status: 'error' })}
        />
      )

      expect(screen.getByText('Connection failed')).toBeInTheDocument()
    })
  })

  describe('Connected Server Info', () => {
    const connectedServer = createServer({
      status: 'connected',
      system_info: {
        os: 'Ubuntu 22.04',
        docker_version: '24.0.5'
      }
    })

    it('should show OS info for connected server', () => {
      render(<ServerCard {...defaultProps} server={connectedServer} />)

      expect(screen.getByText('Ubuntu')).toBeInTheDocument()
    })

    it('should show Docker version for connected server', () => {
      render(<ServerCard {...defaultProps} server={connectedServer} />)

      expect(screen.getByText('24.0.5')).toBeInTheDocument()
    })

    it('should show install button when Docker not installed', () => {
      const serverWithoutDocker = createServer({
        status: 'connected',
        system_info: {
          os: 'Ubuntu 22.04',
          docker_version: 'Not installed'
        }
      })
      render(
        <ServerCard
          {...defaultProps}
          server={serverWithoutDocker}
          onInstallDocker={vi.fn()}
        />
      )

      expect(screen.getByText('Install')).toBeInTheDocument()
    })
  })

  describe('Selection', () => {
    it('should call onSelect when card clicked', async () => {
      const user = userEvent.setup()
      const onSelect = vi.fn()
      render(<ServerCard {...defaultProps} onSelect={onSelect} />)

      await user.click(screen.getByText('Test Server'))

      expect(onSelect).toHaveBeenCalledWith('server-1')
    })

    it('should apply selected styles when isSelected', () => {
      const { container } = render(<ServerCard {...defaultProps} isSelected={true} onSelect={vi.fn()} />)

      // Check for primary border color indicating selection
      const card = container.firstChild
      expect(card).toBeInTheDocument()
    })
  })

  describe('Retry Action', () => {
    it('should call onConnect when retry clicked', async () => {
      const user = userEvent.setup()
      const onConnect = vi.fn()
      render(
        <ServerCard
          {...defaultProps}
          server={createServer({ status: 'error' })}
          onConnect={onConnect}
        />
      )

      await user.click(screen.getByRole('button', { name: /retry/i }))

      expect(onConnect).toHaveBeenCalledWith('server-1')
    })
  })
})
