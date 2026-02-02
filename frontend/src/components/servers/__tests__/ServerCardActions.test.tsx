/**
 * ServerCardActions Test Suite
 *
 * Tests for the ServerCardActions component with action buttons.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ServerCardActions } from '../ServerCardActions'
import { ServerConnection } from '@/types/server'

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'servers.actions.connectToServer': 'Connect',
        'servers.actions.disconnectFromServer': 'Disconnect',
        'servers.actions.editServer': 'Edit',
        'servers.actions.deleteServer': 'Delete'
      }
      return translations[key] || key
    }
  })
}))

describe('ServerCardActions', () => {
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
    it('should render edit button', () => {
      render(<ServerCardActions {...defaultProps} />)

      expect(screen.getByTitle('Edit')).toBeInTheDocument()
    })

    it('should render delete button', () => {
      render(<ServerCardActions {...defaultProps} />)

      expect(screen.getByTitle('Delete')).toBeInTheDocument()
    })
  })

  describe('Disconnected Server', () => {
    it('should show connect button when disconnected', () => {
      render(
        <ServerCardActions
          {...defaultProps}
          server={createServer({ status: 'disconnected' })}
        />
      )

      expect(screen.getByTitle('Connect')).toBeInTheDocument()
    })

    it('should call onConnect when connect clicked', async () => {
      const user = userEvent.setup()
      const onConnect = vi.fn()
      render(
        <ServerCardActions
          {...defaultProps}
          server={createServer({ status: 'disconnected' })}
          onConnect={onConnect}
        />
      )

      await user.click(screen.getByTitle('Connect'))

      expect(onConnect).toHaveBeenCalledWith('server-1')
    })
  })

  describe('Connected Server', () => {
    it('should show disconnect button when connected', () => {
      render(
        <ServerCardActions
          {...defaultProps}
          server={createServer({ status: 'connected' })}
          onDisconnect={vi.fn()}
        />
      )

      expect(screen.getByTitle('Disconnect')).toBeInTheDocument()
    })

    it('should call onDisconnect when disconnect clicked', async () => {
      const user = userEvent.setup()
      const onDisconnect = vi.fn()
      render(
        <ServerCardActions
          {...defaultProps}
          server={createServer({ status: 'connected' })}
          onDisconnect={onDisconnect}
        />
      )

      await user.click(screen.getByTitle('Disconnect'))

      expect(onDisconnect).toHaveBeenCalledWith('server-1')
    })
  })

  describe('Edit Action', () => {
    it('should call onEdit with server when edit clicked', async () => {
      const user = userEvent.setup()
      const onEdit = vi.fn()
      const server = createServer()
      render(<ServerCardActions {...defaultProps} server={server} onEdit={onEdit} />)

      await user.click(screen.getByTitle('Edit'))

      expect(onEdit).toHaveBeenCalledWith(server)
    })
  })

  describe('Delete Action', () => {
    it('should call onDelete with server id when delete clicked', async () => {
      const user = userEvent.setup()
      const onDelete = vi.fn()
      render(<ServerCardActions {...defaultProps} onDelete={onDelete} />)

      await user.click(screen.getByTitle('Delete'))

      expect(onDelete).toHaveBeenCalledWith('server-1')
    })
  })
})
