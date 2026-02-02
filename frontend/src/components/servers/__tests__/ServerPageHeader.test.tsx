/**
 * ServerPageHeader Test Suite
 *
 * Tests for the ServerPageHeader component including
 * title, search, and action buttons.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ServerPageHeader } from '../ServerPageHeader'

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'servers.title': 'Servers',
        'servers.searchPlaceholder': 'Search servers...',
        'servers.import': 'Import',
        'servers.export': 'Export',
        'common.add': 'Add'
      }
      return translations[key] || key
    }
  })
}))

describe('ServerPageHeader', () => {
  const defaultProps = {
    onAddServer: vi.fn(),
    onExportServers: vi.fn(),
    onImportServers: vi.fn(),
    searchTerm: '',
    onSearchChange: vi.fn()
  }

  describe('Rendering', () => {
    it('should render title', () => {
      render(<ServerPageHeader {...defaultProps} />)

      expect(screen.getByText('Servers')).toBeInTheDocument()
    })

    it('should render search input', () => {
      render(<ServerPageHeader {...defaultProps} />)

      expect(screen.getByPlaceholderText('Search servers...')).toBeInTheDocument()
    })

    it('should render import button', () => {
      render(<ServerPageHeader {...defaultProps} />)

      expect(screen.getByRole('button', { name: /import/i })).toBeInTheDocument()
    })

    it('should render export button', () => {
      render(<ServerPageHeader {...defaultProps} />)

      expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument()
    })

    it('should render add button', () => {
      render(<ServerPageHeader {...defaultProps} />)

      expect(screen.getByRole('button', { name: /add/i })).toBeInTheDocument()
    })
  })

  describe('Actions', () => {
    it('should call onAddServer when add button clicked', async () => {
      const user = userEvent.setup()
      const onAddServer = vi.fn()
      render(<ServerPageHeader {...defaultProps} onAddServer={onAddServer} />)

      await user.click(screen.getByRole('button', { name: /add/i }))

      expect(onAddServer).toHaveBeenCalledTimes(1)
    })

    it('should call onExportServers when export button clicked', async () => {
      const user = userEvent.setup()
      const onExportServers = vi.fn()
      render(<ServerPageHeader {...defaultProps} onExportServers={onExportServers} />)

      await user.click(screen.getByRole('button', { name: /export/i }))

      expect(onExportServers).toHaveBeenCalledTimes(1)
    })

    it('should call onImportServers when import button clicked', async () => {
      const user = userEvent.setup()
      const onImportServers = vi.fn()
      render(<ServerPageHeader {...defaultProps} onImportServers={onImportServers} />)

      await user.click(screen.getByRole('button', { name: /import/i }))

      expect(onImportServers).toHaveBeenCalledTimes(1)
    })
  })

  describe('Search', () => {
    it('should display current search term', () => {
      render(<ServerPageHeader {...defaultProps} searchTerm="test" />)

      expect(screen.getByDisplayValue('test')).toBeInTheDocument()
    })

    it('should call onSearchChange when typing', async () => {
      const user = userEvent.setup()
      const onSearchChange = vi.fn()
      render(<ServerPageHeader {...defaultProps} onSearchChange={onSearchChange} />)

      await user.type(screen.getByPlaceholderText('Search servers...'), 'a')

      expect(onSearchChange).toHaveBeenCalled()
    })
  })
})
