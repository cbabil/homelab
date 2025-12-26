/**
 * ServersPage Test Suite
 * 
 * Comprehensive tests for ServersPage component including server management,
 * search functionality, statistics display, and CRUD operations.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { ServersPage } from './ServersPage'

// Mock server data
const mockServers = [
  { id: '1', name: 'Server 1', status: 'connected' },
  { id: '2', name: 'Server 2', status: 'disconnected' }
]

// Mock useServers hook
const mockHandlers = {
  handleAddServer: vi.fn(),
  handleEditServer: vi.fn(),
  handleDeleteServer: vi.fn(),
  handleConnectServer: vi.fn(),
  handleSaveServer: vi.fn()
}

const mockUseServers = vi.fn(() => ({
  filteredServers: mockServers,
  searchTerm: '',
  setSearchTerm: vi.fn(),
  isFormOpen: false,
  setIsFormOpen: vi.fn(),
  editingServer: null,
  connectedCount: 1,
  totalServers: 2,
  healthPercentage: 85,
  ...mockHandlers
}))

vi.mock('@/hooks/useServers', () => ({
  useServers: mockUseServers
}))

// Mock components
vi.mock('@/components/servers/ServerPageHeader', () => ({
  ServerPageHeader: ({ onAddServer }: { onAddServer: () => void }) => (
    <div data-testid="server-page-header">
      <button onClick={onAddServer}>Add Server</button>
    </div>
  )
}))

vi.mock('@/components/servers/ServerSearchBar', () => ({
  ServerSearchBar: ({ 
    searchTerm, 
    onSearchChange, 
    resultCount, 
    totalCount 
  }: {
    searchTerm: string
    onSearchChange: (term: string) => void
    resultCount: number
    totalCount: number
  }) => (
    <div data-testid="server-search-bar">
      <input 
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
        placeholder="Search servers"
        data-testid="search-input"
      />
      <span>Showing {resultCount} of {totalCount} servers</span>
    </div>
  )
}))

vi.mock('@/components/servers/ServerStatsCard', () => ({
  ServerStatsCard: ({ title, value }: { title: string, value: string | number }) => (
    <div data-testid={`stats-card-${title.toLowerCase().replace(' ', '-')}`}>
      <span>{title}: {value}</span>
    </div>
  )
}))

vi.mock('@/components/servers/ServerGridView', () => ({
  ServerGridView: ({ 
    servers, 
    onEdit, 
    onDelete, 
    onConnect, 
    onAddServer,
    onClearSearch 
  }: {
    servers: any[]
    onEdit: (server: any) => void
    onDelete: (id: string) => void
    onConnect: (id: string) => void
    onAddServer: () => void
    onClearSearch: () => void
  }) => (
    <div data-testid="server-grid-view">
      {servers.map(server => (
        <div key={server.id} data-testid={`server-${server.id}`}>
          <span>{server.name}</span>
          <button onClick={() => onEdit(server)}>Edit</button>
          <button onClick={() => onDelete(server.id)}>Delete</button>
          <button onClick={() => onConnect(server.id)}>Connect</button>
        </div>
      ))}
      <button onClick={onAddServer}>Add Server from Grid</button>
      <button onClick={onClearSearch}>Clear Search</button>
    </div>
  )
}))

vi.mock('@/components/servers/ServerFormDialog', () => ({
  ServerFormDialog: ({ 
    isOpen, 
    onClose, 
    onSave, 
    server, 
    title 
  }: {
    isOpen: boolean
    onClose: () => void
    onSave: (data: any) => void
    server: any
    title: string
  }) => (
    isOpen ? (
      <div data-testid="server-form-dialog">
        <h2>{title}</h2>
        <button onClick={onClose}>Close</button>
        <button onClick={() => onSave({ name: 'New Server' })}>Save</button>
      </div>
    ) : null
  )
}))

describe('ServersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseServers.mockReturnValue({
      filteredServers: mockServers,
      searchTerm: '',
      setSearchTerm: vi.fn(),
      isFormOpen: false,
      setIsFormOpen: vi.fn(),
      editingServer: null,
      connectedCount: 1,
      totalServers: 2,
      healthPercentage: 85,
      ...mockHandlers
    })
  })

  describe('Rendering and UI', () => {
    it('should render servers page correctly', () => {
      render(<ServersPage />)
      
      expect(screen.getByTestId('server-page-header')).toBeInTheDocument()
      expect(screen.getByTestId('server-search-bar')).toBeInTheDocument()
      expect(screen.getByTestId('server-grid-view')).toBeInTheDocument()
    })

    it('should display statistics cards', () => {
      render(<ServersPage />)
      
      expect(screen.getByTestId('stats-card-connected')).toBeInTheDocument()
      expect(screen.getByTestId('stats-card-total-servers')).toBeInTheDocument()
      expect(screen.getByTestId('stats-card-health')).toBeInTheDocument()
      
      expect(screen.getByText(/connected: 1/i)).toBeInTheDocument()
      expect(screen.getByText(/total servers: 2/i)).toBeInTheDocument()
      expect(screen.getByText(/health: 85%/i)).toBeInTheDocument()
    })

    it('should display servers in grid view', () => {
      render(<ServersPage />)
      
      expect(screen.getByTestId('server-1')).toBeInTheDocument()
      expect(screen.getByTestId('server-2')).toBeInTheDocument()
      expect(screen.getByText('Server 1')).toBeInTheDocument()
      expect(screen.getByText('Server 2')).toBeInTheDocument()
    })

    it('should have proper layout structure', () => {
      render(<ServersPage />)
      
      const mainContainer = screen.getByTestId('server-page-header').closest('div.space-y-8')
      expect(mainContainer).toBeInTheDocument()
      
      const statsGrid = screen.getByTestId('stats-card-connected').parentElement
      expect(statsGrid).toHaveClass(
        'grid',
        'grid-cols-1',
        'md:grid-cols-3',
        'gap-6'
      )
    })
  })

  describe('Search Functionality', () => {
    it('should handle search input changes', async () => {
      const setSearchTerm = vi.fn()
      mockUseServers.mockReturnValue({
        ...mockUseServers(),
        setSearchTerm
      })
      
      const user = userEvent.setup()
      render(<ServersPage />)
      
      const searchInput = screen.getByTestId('search-input')
      await user.type(searchInput, 'server 1')
      
      expect(setSearchTerm).toHaveBeenCalledWith('server 1')
    })

    it('should display search results count', () => {
      render(<ServersPage />)
      
      expect(screen.getByText(/showing 2 of 2 servers/i)).toBeInTheDocument()
    })

    it('should handle clear search action', async () => {
      const setSearchTerm = vi.fn()
      mockUseServers.mockReturnValue({
        ...mockUseServers(),
        setSearchTerm
      })
      
      const user = userEvent.setup()
      render(<ServersPage />)
      
      const clearButton = screen.getByRole('button', { name: /clear search/i })
      await user.click(clearButton)
      
      expect(setSearchTerm).toHaveBeenCalledWith('')
    })
  })

  describe('Server Actions', () => {
    it('should handle add server from header', async () => {
      const user = userEvent.setup()
      render(<ServersPage />)
      
      const addButton = screen.getByRole('button', { name: /add server$/i })
      await user.click(addButton)
      
      expect(mockHandlers.handleAddServer).toHaveBeenCalled()
    })

    it('should handle edit server action', async () => {
      const user = userEvent.setup()
      render(<ServersPage />)
      
      const editButtons = screen.getAllByRole('button', { name: /edit/i })
      await user.click(editButtons[0])
      
      expect(mockHandlers.handleEditServer).toHaveBeenCalledWith(mockServers[0])
    })

    it('should handle delete server action', async () => {
      const user = userEvent.setup()
      render(<ServersPage />)
      
      const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
      await user.click(deleteButtons[0])
      
      expect(mockHandlers.handleDeleteServer).toHaveBeenCalledWith('1')
    })

    it('should handle connect server action', async () => {
      const user = userEvent.setup()
      render(<ServersPage />)
      
      const connectButtons = screen.getAllByRole('button', { name: /connect/i })
      await user.click(connectButtons[0])
      
      expect(mockHandlers.handleConnectServer).toHaveBeenCalledWith('1')
    })
  })

  describe('Server Form Dialog', () => {
    it('should not show dialog initially', () => {
      render(<ServersPage />)
      
      expect(screen.queryByTestId('server-form-dialog')).not.toBeInTheDocument()
    })

    it('should show dialog when form is open', () => {
      mockUseServers.mockReturnValue({
        ...mockUseServers(),
        isFormOpen: true
      })
      
      render(<ServersPage />)
      
      expect(screen.getByTestId('server-form-dialog')).toBeInTheDocument()
    })

    it('should show add server title for new server', () => {
      mockUseServers.mockReturnValue({
        ...mockUseServers(),
        isFormOpen: true,
        editingServer: null
      })
      
      render(<ServersPage />)
      
      expect(screen.getByText(/add new server/i)).toBeInTheDocument()
    })

    it('should show edit server title for existing server', () => {
      mockUseServers.mockReturnValue({
        ...mockUseServers(),
        isFormOpen: true,
        editingServer: mockServers[0]
      })
      
      render(<ServersPage />)
      
      expect(screen.getByText(/edit server/i)).toBeInTheDocument()
    })

    it('should handle save server action', async () => {
      const user = userEvent.setup()
      mockUseServers.mockReturnValue({
        ...mockUseServers(),
        isFormOpen: true
      })
      
      render(<ServersPage />)
      
      const saveButton = screen.getByRole('button', { name: /save/i })
      await user.click(saveButton)
      
      expect(mockHandlers.handleSaveServer).toHaveBeenCalledWith({ name: 'New Server' })
    })

    it('should handle close dialog action', async () => {
      const setIsFormOpen = vi.fn()
      mockUseServers.mockReturnValue({
        ...mockUseServers(),
        isFormOpen: true,
        setIsFormOpen
      })
      
      const user = userEvent.setup()
      render(<ServersPage />)
      
      const closeButton = screen.getByRole('button', { name: /close/i })
      await user.click(closeButton)
      
      expect(setIsFormOpen).toHaveBeenCalledWith(false)
    })
  })

  describe('Statistics Updates', () => {
    it('should display updated statistics', () => {
      mockUseServers.mockReturnValue({
        ...mockUseServers(),
        connectedCount: 3,
        totalServers: 5,
        healthPercentage: 90
      })
      
      render(<ServersPage />)
      
      expect(screen.getByText(/connected: 3/i)).toBeInTheDocument()
      expect(screen.getByText(/total servers: 5/i)).toBeInTheDocument()
      expect(screen.getByText(/health: 90%/i)).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('should handle empty servers list', () => {
      mockUseServers.mockReturnValue({
        ...mockUseServers(),
        filteredServers: []
      })
      
      render(<ServersPage />)
      
      expect(screen.queryByTestId('server-1')).not.toBeInTheDocument()
      expect(screen.queryByTestId('server-2')).not.toBeInTheDocument()
    })
  })
})