/**
 * ServerGridView Test Suite
 *
 * Tests for the ServerGridView component that displays
 * servers in a grid with bulk selection support.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ServerGridView } from '../ServerGridView'
import { ServerConnection } from '@/types/server'

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: { count?: number }) => {
      const translations: Record<string, string> = {
        'servers.noServers': 'No servers',
        'servers.noServersDescription': 'Add your first server to get started',
        'servers.noServersFound': 'No servers found',
        'servers.noServersFoundDescription': 'No servers match your search',
        'servers.addServer': 'Add Server',
        'servers.clearSearch': 'Clear Search',
        'servers.selectAll': 'Select All',
        'servers.deselectAll': 'Deselect All',
        'servers.connect': 'Connect',
        'servers.disconnect': 'Disconnect',
        'common.clear': 'Clear'
      }
      if (key === 'servers.selectedCount') {
        return `${options?.count} selected`
      }
      return translations[key] || key
    }
  })
}))

// Mock ServerCard to simplify testing
vi.mock('../ServerCard', () => ({
  ServerCard: ({ server, onSelect, isSelected }: { server: ServerConnection, onSelect?: (id: string) => void, isSelected?: boolean }) => (
    <div
      data-testid={`server-card-${server.id}`}
      data-selected={isSelected}
      onClick={() => onSelect?.(server.id)}
    >
      {server.name}
    </div>
  )
}))

describe('ServerGridView', () => {
  const createServer = (id: string, name: string): ServerConnection => ({
    id,
    name,
    host: '192.168.1.100',
    port: 22,
    username: 'admin',
    auth_type: 'password',
    status: 'disconnected',
    created_at: '2024-01-01T00:00:00Z',
    docker_installed: false
  })

  const defaultProps = {
    servers: [],
    searchTerm: '',
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    onConnect: vi.fn(),
    onAddServer: vi.fn(),
    onClearSearch: vi.fn()
  }

  describe('Empty State', () => {
    it('should show empty state when no servers', () => {
      render(<ServerGridView {...defaultProps} />)

      expect(screen.getByText('No servers')).toBeInTheDocument()
      expect(screen.getByText('Add your first server to get started')).toBeInTheDocument()
    })

    it('should show add server button when no servers', () => {
      render(<ServerGridView {...defaultProps} />)

      expect(screen.getByRole('button', { name: /add server/i })).toBeInTheDocument()
    })

    it('should call onAddServer when add button clicked', async () => {
      const user = userEvent.setup()
      const onAddServer = vi.fn()
      render(<ServerGridView {...defaultProps} onAddServer={onAddServer} />)

      await user.click(screen.getByRole('button', { name: /add server/i }))

      expect(onAddServer).toHaveBeenCalledTimes(1)
    })
  })

  describe('Empty Search Results', () => {
    it('should show no results message when search has no matches', () => {
      render(<ServerGridView {...defaultProps} searchTerm="nonexistent" />)

      expect(screen.getByText('No servers found')).toBeInTheDocument()
      expect(screen.getByText('No servers match your search')).toBeInTheDocument()
    })

    it('should show clear search button when searching', () => {
      render(<ServerGridView {...defaultProps} searchTerm="test" />)

      expect(screen.getByRole('button', { name: /clear search/i })).toBeInTheDocument()
    })

    it('should call onClearSearch when clear button clicked', async () => {
      const user = userEvent.setup()
      const onClearSearch = vi.fn()
      render(<ServerGridView {...defaultProps} searchTerm="test" onClearSearch={onClearSearch} />)

      await user.click(screen.getByRole('button', { name: /clear search/i }))

      expect(onClearSearch).toHaveBeenCalledTimes(1)
    })
  })

  describe('Server Grid', () => {
    const servers = [
      createServer('server-1', 'Server 1'),
      createServer('server-2', 'Server 2'),
      createServer('server-3', 'Server 3')
    ]

    it('should render server cards', () => {
      render(<ServerGridView {...defaultProps} servers={servers} />)

      expect(screen.getByTestId('server-card-server-1')).toBeInTheDocument()
      expect(screen.getByTestId('server-card-server-2')).toBeInTheDocument()
      expect(screen.getByTestId('server-card-server-3')).toBeInTheDocument()
    })

    it('should render server names', () => {
      render(<ServerGridView {...defaultProps} servers={servers} />)

      expect(screen.getByText('Server 1')).toBeInTheDocument()
      expect(screen.getByText('Server 2')).toBeInTheDocument()
      expect(screen.getByText('Server 3')).toBeInTheDocument()
    })
  })

  describe('Bulk Selection', () => {
    const servers = [
      createServer('server-1', 'Server 1'),
      createServer('server-2', 'Server 2')
    ]

    it('should show bulk action bar when servers selected', () => {
      render(
        <ServerGridView
          {...defaultProps}
          servers={servers}
          selectedIds={new Set(['server-1'])}
        />
      )

      expect(screen.getByText('1 selected')).toBeInTheDocument()
    })

    it('should show correct count for multiple selections', () => {
      render(
        <ServerGridView
          {...defaultProps}
          servers={servers}
          selectedIds={new Set(['server-1', 'server-2'])}
        />
      )

      expect(screen.getByText('2 selected')).toBeInTheDocument()
    })

    it('should call onSelectServer when card clicked', async () => {
      const user = userEvent.setup()
      const onSelectServer = vi.fn()
      render(
        <ServerGridView
          {...defaultProps}
          servers={servers}
          onSelectServer={onSelectServer}
        />
      )

      await user.click(screen.getByTestId('server-card-server-1'))

      expect(onSelectServer).toHaveBeenCalledWith('server-1')
    })

    it('should show select all button in bulk bar', () => {
      render(
        <ServerGridView
          {...defaultProps}
          servers={servers}
          selectedIds={new Set(['server-1'])}
          onSelectAll={vi.fn()}
        />
      )

      expect(screen.getByText('Select All')).toBeInTheDocument()
    })

    it('should show deselect all when all selected', () => {
      render(
        <ServerGridView
          {...defaultProps}
          servers={servers}
          selectedIds={new Set(['server-1', 'server-2'])}
          onSelectAll={vi.fn()}
        />
      )

      expect(screen.getByText('Deselect All')).toBeInTheDocument()
    })

    it('should call onBulkConnect when connect clicked', async () => {
      const user = userEvent.setup()
      const onBulkConnect = vi.fn()
      render(
        <ServerGridView
          {...defaultProps}
          servers={servers}
          selectedIds={new Set(['server-1'])}
          onBulkConnect={onBulkConnect}
        />
      )

      await user.click(screen.getByRole('button', { name: /connect/i }))

      expect(onBulkConnect).toHaveBeenCalledTimes(1)
    })

    it('should call onClearSelection when clear clicked', async () => {
      const user = userEvent.setup()
      const onClearSelection = vi.fn()
      render(
        <ServerGridView
          {...defaultProps}
          servers={servers}
          selectedIds={new Set(['server-1'])}
          onClearSelection={onClearSelection}
        />
      )

      await user.click(screen.getByRole('button', { name: /clear/i }))

      expect(onClearSelection).toHaveBeenCalledTimes(1)
    })
  })
})
