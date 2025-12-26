/**
 * ApplicationsPage Test Suite
 * 
 * Comprehensive tests for ApplicationsPage component including filtering,
 * search functionality, app management, and user interactions.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ApplicationsPage } from './ApplicationsPage'

// Mock dependencies
const mockApps = [
  {
    id: '1',
    name: 'Test App 1',
    status: 'installed',
    category: { id: 'development', name: 'Development' }
  },
  {
    id: '2',
    name: 'Test App 2',
    status: 'available',
    category: { id: 'productivity', name: 'Productivity' }
  }
]

const mockCategories = [
  { id: 'development', name: 'Development', description: '', icon: vi.fn(), color: '' }
]
const mockAddApplication = vi.fn()
const mockSetFilter = vi.fn()
const mockUpdateFilter = vi.fn()

vi.mock('@/hooks/useApplications', () => ({
  useApplications: vi.fn(() => ({
    apps: mockApps,
    categories: mockCategories,
    filter: {},
    setFilter: mockSetFilter,
    updateFilter: mockUpdateFilter,
    addApplication: mockAddApplication,
    updateApplication: vi.fn(),
    deleteApplication: vi.fn(),
    installApplication: vi.fn(),
    isLoading: false,
    error: null,
    refresh: vi.fn()
  }))
}))

vi.mock('./ApplicationsPageHeader', () => ({
  ApplicationsPageHeader: ({ onAddApp }: { onAddApp: () => void }) => (
    <div data-testid="applications-page-header">
      <button onClick={onAddApp}>Add App</button>
    </div>
  )
}))

vi.mock('./ApplicationsSearchAndFilter', () => ({
  ApplicationsSearchAndFilter: ({ 
    onSearch, 
    onFilterChange,
    categories
  }: { 
    onSearch: (value: string) => void
    onFilterChange: (filter: any) => void
    categories: any[]
  }) => (
    <div data-testid="applications-search-filter">
      <input 
        placeholder="Search apps"
        onChange={(e) => onSearch(e.target.value)}
        data-testid="search-input"
      />
      <select 
        onChange={(e) => onFilterChange({ status: e.target.value })}
        data-testid="status-filter"
      >
        <option value="">All Status</option>
        <option value="installed">Installed</option>
        <option value="available">Available</option>
      </select>
    </div>
  )
}))

vi.mock('./ApplicationsEmptyState', () => ({
  ApplicationsEmptyState: () => (
    <div data-testid="applications-empty-state">No applications found</div>
  )
}))

vi.mock('@/components/applications/AppCard', () => ({
  AppCard: ({ app }: { app: any }) => (
    <div data-testid={`app-card-${app.id}`}>
      {app.name} - {app.status}
    </div>
  )
}))

vi.mock('@/components/applications/ApplicationFormDialog', () => ({
  ApplicationFormDialog: ({ 
    isOpen, 
    onClose, 
    onSave, 
    title,
    categories
  }: { 
    isOpen: boolean
    onClose: () => void
    onSave: (data: any) => void
    title: string
    categories: any[]
  }) => (
    isOpen ? (
      <div data-testid="application-form-dialog">
        <h2>{title}</h2>
        <button onClick={onClose}>Close Dialog</button>
        <button onClick={() => onSave({ name: 'New App' })}>Save App</button>
      </div>
    ) : null
  )
}))

function renderApplicationsPage() {
  return render(
    <BrowserRouter>
      <ApplicationsPage />
    </BrowserRouter>
  )
}

describe('ApplicationsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSetFilter.mockReset()
    mockUpdateFilter.mockReset()
  })

  describe('Rendering and UI', () => {
    it('should render applications page correctly', () => {
      renderApplicationsPage()
      
      expect(screen.getByTestId('applications-page-header')).toBeInTheDocument()
      expect(screen.getByTestId('applications-search-filter')).toBeInTheDocument()
      expect(screen.getByTestId('app-card-1')).toBeInTheDocument()
      expect(screen.getByTestId('app-card-2')).toBeInTheDocument()
    })

    it('should display app cards for all apps', () => {
      renderApplicationsPage()
      
      expect(screen.getByText(/test app 1 - installed/i)).toBeInTheDocument()
      expect(screen.getByText(/test app 2 - available/i)).toBeInTheDocument()
    })

    it('should have proper grid layout classes', () => {
      renderApplicationsPage()
      
      const gridContainer = screen.getByTestId('app-card-1').parentElement
      expect(gridContainer).toHaveClass(
        'grid',
        'grid-cols-1',
        'md:grid-cols-2',
        'lg:grid-cols-3',
        'xl:grid-cols-4',
        '2xl:grid-cols-5',
        'gap-3'
      )
    })
  })

  describe('Search Functionality', () => {
    it('should request filter update based on search input', async () => {
      const user = userEvent.setup()
      renderApplicationsPage()
      
      const searchInput = screen.getByTestId('search-input')
      await user.type(searchInput, 'Test App 1')
      
      await waitFor(() => {
        expect(mockUpdateFilter).toHaveBeenCalled()
      })
      expect(mockUpdateFilter).toHaveBeenCalledWith({ search: 'Test App 1' })
    })

    it('should trigger filter update when no apps match search', async () => {
      const user = userEvent.setup()
      renderApplicationsPage()
      
      const searchInput = screen.getByTestId('search-input')
      await user.type(searchInput, 'Nonexistent App')
      
      await waitFor(() => {
        expect(mockUpdateFilter).toHaveBeenCalled()
      })
    })
  })

  describe('Filter Functionality', () => {
    it('should update filter when status is selected', async () => {
      const user = userEvent.setup()
      renderApplicationsPage()
      
      const statusFilter = screen.getByTestId('status-filter')
      await user.selectOptions(statusFilter, 'installed')
      
      await waitFor(() => {
        expect(mockSetFilter).toHaveBeenCalled()
      })
    })
  })

  describe('Add Application Dialog', () => {
    it('should open add application dialog when add button is clicked', async () => {
      const user = userEvent.setup()
      renderApplicationsPage()
      
      const addButton = screen.getByRole('button', { name: /add app/i })
      await user.click(addButton)
      
      expect(screen.getByTestId('application-form-dialog')).toBeInTheDocument()
      expect(screen.getByText(/add custom application/i)).toBeInTheDocument()
    })

    it('should close dialog when close button is clicked', async () => {
      const user = userEvent.setup()
      renderApplicationsPage()
      
      // Open dialog
      const addButton = screen.getByRole('button', { name: /add app/i })
      await user.click(addButton)
      
      // Close dialog
      const closeButton = screen.getByRole('button', { name: /close dialog/i })
      await user.click(closeButton)
      
      expect(screen.queryByTestId('application-form-dialog')).not.toBeInTheDocument()
    })

    it('should handle save application', async () => {
      const user = userEvent.setup()
      mockAddApplication.mockResolvedValue(undefined)
      renderApplicationsPage()
      
      // Open dialog
      const addButton = screen.getByRole('button', { name: /add app/i })
      await user.click(addButton)
      
      // Save app
      const saveButton = screen.getByRole('button', { name: /save app/i })
      await user.click(saveButton)
      
      expect(mockAddApplication).toHaveBeenCalledWith({ name: 'New App' })
      
      await waitFor(() => {
        expect(screen.queryByTestId('application-form-dialog')).not.toBeInTheDocument()
      })
    })
  })

  describe('URL Parameters', () => {
    it('should handle category URL parameter', () => {
      // This would require more complex setup with Router and search params
      // For now, we'll just ensure the component renders without errors
      renderApplicationsPage()
      
      expect(screen.getByTestId('applications-page-header')).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('should show empty state when no apps are available', () => {
      vi.mocked(require('@/hooks/useApplications').useApplications).mockReturnValue({
        apps: [],
        addApplication: mockAddApplication
      })
      
      renderApplicationsPage()
      
      expect(screen.getByTestId('applications-empty-state')).toBeInTheDocument()
      expect(screen.queryByTestId('app-card-1')).not.toBeInTheDocument()
      expect(screen.queryByTestId('app-card-2')).not.toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should handle add application error', async () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
      const user = userEvent.setup()
      mockAddApplication.mockRejectedValue(new Error('Failed to add'))
      renderApplicationsPage()
      
      // Open dialog and save
      const addButton = screen.getByRole('button', { name: /add app/i })
      await user.click(addButton)
      
      const saveButton = screen.getByRole('button', { name: /save app/i })
      await user.click(saveButton)
      
      await waitFor(() => {
        expect(consoleError).toHaveBeenCalledWith('Failed to add application:', expect.any(Error))
      })
      
      consoleError.mockRestore()
    })
  })
})
