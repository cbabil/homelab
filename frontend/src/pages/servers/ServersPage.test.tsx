/**
 * ServersPage Test Suite
 *
 * Comprehensive tests for ServersPage component including server management,
 * search functionality, and CRUD operations.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ServersPage } from './ServersPage'
import { ToastProvider } from '@/components/ui/Toast'

// Mock server data
const mockServers = [
  {
    id: '1',
    name: 'Server 1',
    host: 'localhost',
    port: 22,
    username: 'admin',
    auth_type: 'password' as const,
    status: 'connected' as const,
    created_at: '2024-01-01',
    docker_installed: false
  },
  {
    id: '2',
    name: 'Server 2',
    host: 'localhost',
    port: 22,
    username: 'admin',
    auth_type: 'password' as const,
    status: 'disconnected' as const,
    created_at: '2024-01-01',
    docker_installed: false
  }
]

// Mock useServers hook
const { mockUseServers, mockHandlers } = vi.hoisted(() => {
  const mockHandlers = {
    handleAddServer: vi.fn(),
    handleEditServer: vi.fn(),
    handleDeleteServer: vi.fn(),
    handleConnectServer: vi.fn().mockResolvedValue({ success: true }),
    handleDisconnectServer: vi.fn(),
    handleInstallDocker: vi.fn(),
    handleSaveServer: vi.fn(),
    refreshServers: vi.fn(),
    handleSelectServer: vi.fn(),
    handleSelectAll: vi.fn(),
    handleClearSelection: vi.fn(),
    handleBulkConnect: vi.fn(),
    handleBulkDisconnect: vi.fn()
  }

  const mockUseServers = vi.fn(() => ({
    filteredServers: mockServers,
    searchTerm: '',
    setSearchTerm: vi.fn(),
    isFormOpen: false,
    setIsFormOpen: vi.fn(),
    editingServer: undefined as typeof mockServers[0] | undefined,
    servers: mockServers,
    selectedIds: new Set<string>(),
    ...mockHandlers
  }))

  return { mockUseServers, mockHandlers }
})

vi.mock('@/hooks/useServers', () => ({
  useServers: mockUseServers
}))

// Mock services
vi.mock('@/services/serverExportService', () => ({
  serverExportService: {
    exportUserServers: vi.fn().mockReturnValue({ success: true, message: 'Exported', filename: 'servers.json' }),
    importServers: vi.fn().mockResolvedValue([])
  }
}))

// Mock SettingsProvider
vi.mock('@/providers/SettingsProvider', () => ({
  useSettingsContext: () => ({
    settings: {
      ui: { refreshRate: 60 },
      applications: { autoRefreshStatus: true }
    },
    updateSettings: vi.fn(),
    isLoading: false,
    error: null
  })
}))

// Mock useAgentStatus hook
vi.mock('@/hooks/useAgentStatus', () => ({
  useAgentStatus: () => ({
    agentStatuses: new Map(),
    installAgent: vi.fn(),
    uninstallAgent: vi.fn(),
    refreshAllAgentStatuses: vi.fn()
  })
}))

// Mock useServerDeletion hook
vi.mock('@/hooks/useServerDeletion', () => ({
  useServerDeletion: () => ({
    deletingServer: null,
    handleOpenDeleteDialog: vi.fn(),
    handleCloseDeleteDialog: vi.fn()
  })
}))

// Mock components
vi.mock('@/components/servers/ServerPageHeader', () => ({
  ServerPageHeader: ({ onAddServer }: { onAddServer: () => void }) => (
    <div data-testid="server-page-header">
      <button onClick={onAddServer}>Add Server</button>
    </div>
  )
}))

interface MockServer {
  id: string
  name: string
  status: string
}

vi.mock('@/components/servers/ServerGridView', () => ({
  ServerGridView: ({
    servers,
    onEdit,
    onDelete,
    onConnect,
    onAddServer,
    onClearSearch
  }: {
    servers: MockServer[]
    onEdit: (server: MockServer) => void
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
    title
  }: {
    isOpen: boolean
    onClose: () => void
    onSave: (data: Record<string, unknown>) => void
    server: MockServer | null
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

vi.mock('@/components/ui/TablePagination', () => ({
  TablePagination: () => <div data-testid="table-pagination" />
}))

function renderServersPage() {
  return render(
    <BrowserRouter>
      <ToastProvider>
        <ServersPage />
      </ToastProvider>
    </BrowserRouter>
  )
}

describe('ServersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseServers.mockReturnValue({
      filteredServers: mockServers,
      searchTerm: '',
      setSearchTerm: vi.fn(),
      isFormOpen: false,
      setIsFormOpen: vi.fn(),
      editingServer: undefined,
      servers: mockServers,
      selectedIds: new Set<string>(),
      ...mockHandlers
    })
  })

  describe('Rendering and UI', () => {
    it('should render servers page correctly', () => {
      renderServersPage()

      expect(screen.getByTestId('server-page-header')).toBeInTheDocument()
      expect(screen.getByTestId('server-grid-view')).toBeInTheDocument()
    })

    it('should display servers in grid view', () => {
      renderServersPage()

      expect(screen.getByTestId('server-1')).toBeInTheDocument()
      expect(screen.getByTestId('server-2')).toBeInTheDocument()
      expect(screen.getByText('Server 1')).toBeInTheDocument()
      expect(screen.getByText('Server 2')).toBeInTheDocument()
    })

    it('should display server count', () => {
      renderServersPage()

      // Server count is displayed via translation
      expect(screen.getByText(/2 servers/i)).toBeInTheDocument()
    })

    it('should show pagination when servers exist', () => {
      renderServersPage()

      expect(screen.getByTestId('table-pagination')).toBeInTheDocument()
    })
  })

  describe('Server Actions', () => {
    it('should handle add server from header', async () => {
      const user = userEvent.setup()
      renderServersPage()

      const addButton = screen.getByRole('button', { name: /add server$/i })
      await user.click(addButton)

      expect(mockHandlers.handleAddServer).toHaveBeenCalled()
    })

    it('should handle edit server action', async () => {
      const user = userEvent.setup()
      renderServersPage()

      const editButtons = screen.getAllByRole('button', { name: /edit/i })
      await user.click(editButtons[0])

      expect(mockHandlers.handleEditServer).toHaveBeenCalledWith(mockServers[0])
    })

    it('should handle delete server action', async () => {
      const user = userEvent.setup()
      renderServersPage()

      const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
      await user.click(deleteButtons[0])

      expect(mockHandlers.handleDeleteServer).toHaveBeenCalledWith('1')
    })

    it('should handle connect server action', async () => {
      const user = userEvent.setup()
      renderServersPage()

      const connectButtons = screen.getAllByRole('button', { name: /connect/i })
      await user.click(connectButtons[0])

      await waitFor(() => {
        expect(mockHandlers.handleConnectServer).toHaveBeenCalledWith('1')
      })
    })

    it('should handle clear search action', async () => {
      const setSearchTerm = vi.fn()
      mockUseServers.mockReturnValue({
        ...mockUseServers(),
        setSearchTerm
      })

      const user = userEvent.setup()
      renderServersPage()

      const clearButton = screen.getByRole('button', { name: /clear search/i })
      await user.click(clearButton)

      expect(setSearchTerm).toHaveBeenCalledWith('')
    })
  })

  describe('Server Form Dialog', () => {
    it('should not show dialog initially', () => {
      renderServersPage()

      expect(screen.queryByTestId('server-form-dialog')).not.toBeInTheDocument()
    })

    it('should show dialog when form is open', () => {
      mockUseServers.mockReturnValue({
        ...mockUseServers(),
        isFormOpen: true
      })

      renderServersPage()

      expect(screen.getByTestId('server-form-dialog')).toBeInTheDocument()
    })

    it('should show add server title for new server', () => {
      const baseReturnValue = mockUseServers()
      mockUseServers.mockReturnValue({
        ...baseReturnValue,
        isFormOpen: true,
        editingServer: undefined
      })

      renderServersPage()

      // Title comes from translation: t('servers.addServer')
      expect(screen.getByRole('heading', { name: /add server/i })).toBeInTheDocument()
    })

    it('should show edit server title for existing server', () => {
      const baseReturnValue = mockUseServers()
      mockUseServers.mockReturnValue({
        ...baseReturnValue,
        isFormOpen: true,
        editingServer: mockServers[0]
      })

      renderServersPage()

      // Title comes from translation: t('servers.editServer')
      expect(screen.getByRole('heading', { name: /edit server/i })).toBeInTheDocument()
    })

    it('should handle save server action', async () => {
      const user = userEvent.setup()
      mockUseServers.mockReturnValue({
        ...mockUseServers(),
        isFormOpen: true
      })

      renderServersPage()

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
      renderServersPage()

      const closeButton = screen.getByRole('button', { name: /close/i })
      await user.click(closeButton)

      expect(setIsFormOpen).toHaveBeenCalledWith(false)
    })
  })

  describe('Empty State', () => {
    it('should handle empty servers list', () => {
      mockUseServers.mockReturnValue({
        ...mockUseServers(),
        filteredServers: [],
        servers: []
      })

      renderServersPage()

      expect(screen.queryByTestId('server-1')).not.toBeInTheDocument()
      expect(screen.queryByTestId('server-2')).not.toBeInTheDocument()
    })

    it('should not show pagination when no servers', () => {
      mockUseServers.mockReturnValue({
        ...mockUseServers(),
        filteredServers: [],
        servers: []
      })

      renderServersPage()

      expect(screen.queryByTestId('table-pagination')).not.toBeInTheDocument()
    })
  })

  describe('Search Results', () => {
    it('should display filtered count when searching', () => {
      mockUseServers.mockReturnValue({
        ...mockUseServers(),
        filteredServers: [mockServers[0]],
        searchTerm: 'Server 1'
      })

      renderServersPage()

      // Should show "1 of 2 servers" when filtered
      expect(screen.getByText(/1 of 2 servers/i)).toBeInTheDocument()
    })
  })
})
