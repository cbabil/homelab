/**
 * ServerFormDialog Component Tests
 *
 * Unit tests for the server form dialog including form rendering,
 * validation, and submission.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { ServerFormDialog } from '../ServerFormDialog'

// Mock useServerForm hook
const mockHandleInputChange = vi.fn()
const mockHandleAuthTypeChange = vi.fn()
const mockHandleCredentialChange = vi.fn()
const mockResetForm = vi.fn()

vi.mock('@/hooks/useServerForm', () => ({
  useServerForm: vi.fn((server) => ({
    formData: {
      name: server?.name || '',
      host: server?.host || '',
      port: server?.port || 22,
      username: server?.username || '',
      auth_type: server?.auth_type || 'password',
      credentials: {
        password: '',
        private_key: '',
        passphrase: ''
      }
    },
    handleInputChange: mockHandleInputChange,
    handleAuthTypeChange: mockHandleAuthTypeChange,
    handleCredentialChange: mockHandleCredentialChange,
    resetForm: mockResetForm
  }))
}))

// Mock useServerProvisioning hook
const mockStartProvisioning = vi.fn()
const mockCancel = vi.fn()
const mockReset = vi.fn()

vi.mock('@/hooks/useServerProvisioning', () => ({
  useServerProvisioning: vi.fn(() => ({
    state: {
      isProvisioning: false,
      currentStep: 'connection',
      steps: [],
      requiresDecision: undefined,
      canRetry: false,
      dockerInstalled: false
    },
    startProvisioning: mockStartProvisioning,
    installDocker: vi.fn(),
    skipDocker: vi.fn(),
    installAgent: vi.fn(),
    skipAgent: vi.fn(),
    retry: vi.fn(),
    cancel: mockCancel,
    reset: mockReset
  }))
}))

describe('ServerFormDialog', () => {
  const mockOnClose = vi.fn()
  const mockOnSave = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockOnSave.mockResolvedValue('srv-123')
  })

  describe('rendering', () => {
    it('should not render dialog content when isOpen is false', () => {
      render(
        <ServerFormDialog
          isOpen={false}
          onClose={mockOnClose}
          onSave={mockOnSave}
          title="Add Server"
        />
      )

      expect(screen.queryByText('Add Server')).not.toBeInTheDocument()
    })

    it('should render dialog when isOpen is true', () => {
      render(
        <ServerFormDialog
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          title="Add Server"
        />
      )

      expect(screen.getByText('Add Server')).toBeInTheDocument()
    })

    it('should render all form fields', () => {
      render(
        <ServerFormDialog
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          title="Add Server"
        />
      )

      // Use getByRole with name option for better specificity
      expect(screen.getByRole('textbox', { name: /^Name/ })).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /^Host/ })).toBeInTheDocument()
      expect(screen.getByRole('spinbutton', { name: /^Port/ })).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /^Username/ })).toBeInTheDocument()
    })

    it('should render Cancel and Add buttons', () => {
      render(
        <ServerFormDialog
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          title="Add Server"
        />
      )

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /add/i })).toBeInTheDocument()
    })

    it('should show Save button when editing existing server', () => {
      const existingServer = {
        id: 'srv-123',
        name: 'Test Server',
        host: '192.168.1.100',
        port: 22,
        username: 'admin',
        auth_type: 'password' as const,
        status: 'disconnected' as const,
        created_at: '2024-01-01T00:00:00Z',
        docker_installed: false
      }

      render(
        <ServerFormDialog
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          server={existingServer}
          title="Edit Server"
        />
      )

      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument()
    })
  })

  describe('close functionality', () => {
    it('should call onClose when X button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <ServerFormDialog
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          title="Add Server"
        />
      )

      // Find close button by looking for the X icon button
      const closeButton = screen.getByRole('button', { name: '' })
      await user.click(closeButton)

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should call onClose when Cancel button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <ServerFormDialog
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          title="Add Server"
        />
      )

      await user.click(screen.getByRole('button', { name: /cancel/i }))

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })
  })

  describe('form submission', () => {
    it('should have Add button disabled when form is incomplete', () => {
      render(
        <ServerFormDialog
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          title="Add Server"
        />
      )

      const addButton = screen.getByRole('button', { name: /add/i })
      expect(addButton).toBeDisabled()
    })

    it('should call onSave with preGeneratedServerId when form is submitted for new server', async () => {
      const user = userEvent.setup()

      // Mock complete form data
      const { useServerForm } = await import('@/hooks/useServerForm')
      vi.mocked(useServerForm).mockReturnValue({
        formData: {
          name: 'Test Server',
          host: '192.168.1.100',
          port: 22,
          username: 'admin',
          auth_type: 'password',
          credentials: {
            password: 'secret123',
            private_key: '',
            passphrase: ''
          }
        },
        handleInputChange: mockHandleInputChange,
        handleAuthTypeChange: mockHandleAuthTypeChange,
        handleCredentialChange: mockHandleCredentialChange,
        resetForm: mockResetForm
      })

      render(
        <ServerFormDialog
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          title="Add Server"
        />
      )

      const addButton = screen.getByRole('button', { name: /add/i })
      await user.click(addButton)

      await waitFor(() => {
        // For new servers, onSave is called with undefined statusCallback and a preGeneratedServerId
        expect(mockOnSave).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Test Server',
            host: '192.168.1.100',
            port: 22,
            username: 'admin',
            auth_type: 'password'
          }),
          undefined,
          undefined,
          expect.any(String) // preGeneratedServerId
        )
      })
    })

    it('should start provisioning after successful save for new server', async () => {
      const user = userEvent.setup()

      const { useServerForm } = await import('@/hooks/useServerForm')
      vi.mocked(useServerForm).mockReturnValue({
        formData: {
          name: 'Test Server',
          host: '192.168.1.100',
          port: 22,
          username: 'admin',
          auth_type: 'password',
          credentials: {
            password: 'secret123',
            private_key: '',
            passphrase: ''
          }
        },
        handleInputChange: mockHandleInputChange,
        handleAuthTypeChange: mockHandleAuthTypeChange,
        handleCredentialChange: mockHandleCredentialChange,
        resetForm: mockResetForm
      })

      render(
        <ServerFormDialog
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          title="Add Server"
        />
      )

      await user.click(screen.getByRole('button', { name: /add/i }))

      await waitFor(() => {
        // For new servers, startProvisioning should be called instead of onClose
        expect(mockStartProvisioning).toHaveBeenCalledWith(expect.any(String))
      })
      // Dialog should not close - it stays open for provisioning
      expect(mockOnClose).not.toHaveBeenCalled()
    })

    it('should call onClose after successful save for editing existing server', async () => {
      const user = userEvent.setup()
      const existingServer = {
        id: 'srv-123',
        name: 'Test Server',
        host: '192.168.1.100',
        port: 22,
        username: 'admin',
        auth_type: 'password' as const,
        status: 'disconnected' as const,
        created_at: '2024-01-01T00:00:00Z',
        docker_installed: false
      }

      const { useServerForm } = await import('@/hooks/useServerForm')
      vi.mocked(useServerForm).mockReturnValue({
        formData: {
          name: 'Test Server',
          host: '192.168.1.100',
          port: 22,
          username: 'admin',
          auth_type: 'password',
          credentials: {
            password: 'secret123',
            private_key: '',
            passphrase: ''
          }
        },
        handleInputChange: mockHandleInputChange,
        handleAuthTypeChange: mockHandleAuthTypeChange,
        handleCredentialChange: mockHandleCredentialChange,
        resetForm: mockResetForm
      })

      render(
        <ServerFormDialog
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          server={existingServer}
          title="Edit Server"
        />
      )

      await user.click(screen.getByRole('button', { name: /save/i }))

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled()
      })
      // Provisioning should NOT start for edits
      expect(mockStartProvisioning).not.toHaveBeenCalled()
    })

    it('should show error message when save fails', async () => {
      const user = userEvent.setup()
      mockOnSave.mockRejectedValue(new Error('Connection failed'))

      const { useServerForm } = await import('@/hooks/useServerForm')
      vi.mocked(useServerForm).mockReturnValue({
        formData: {
          name: 'Test Server',
          host: '192.168.1.100',
          port: 22,
          username: 'admin',
          auth_type: 'password',
          credentials: {
            password: 'secret123',
            private_key: '',
            passphrase: ''
          }
        },
        handleInputChange: mockHandleInputChange,
        handleAuthTypeChange: mockHandleAuthTypeChange,
        handleCredentialChange: mockHandleCredentialChange,
        resetForm: mockResetForm
      })

      render(
        <ServerFormDialog
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          title="Add Server"
        />
      )

      await user.click(screen.getByRole('button', { name: /add/i }))

      await waitFor(() => {
        expect(screen.getByText('Connection failed')).toBeInTheDocument()
      })
    })

    it('should not close dialog when save fails', async () => {
      const user = userEvent.setup()
      mockOnSave.mockRejectedValue(new Error('Connection failed'))

      const { useServerForm } = await import('@/hooks/useServerForm')
      vi.mocked(useServerForm).mockReturnValue({
        formData: {
          name: 'Test Server',
          host: '192.168.1.100',
          port: 22,
          username: 'admin',
          auth_type: 'password',
          credentials: {
            password: 'secret123',
            private_key: '',
            passphrase: ''
          }
        },
        handleInputChange: mockHandleInputChange,
        handleAuthTypeChange: mockHandleAuthTypeChange,
        handleCredentialChange: mockHandleCredentialChange,
        resetForm: mockResetForm
      })

      render(
        <ServerFormDialog
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          title="Add Server"
        />
      )

      await user.click(screen.getByRole('button', { name: /add/i }))

      await waitFor(() => {
        expect(screen.getByText('Connection failed')).toBeInTheDocument()
      })

      // Dialog should still be open
      expect(mockOnClose).not.toHaveBeenCalled()
    })

    it('should disable buttons while saving for edit mode', async () => {
      const user = userEvent.setup()
      const existingServer = {
        id: 'srv-123',
        name: 'Test Server',
        host: '192.168.1.100',
        port: 22,
        username: 'admin',
        auth_type: 'password' as const,
        status: 'disconnected' as const,
        created_at: '2024-01-01T00:00:00Z',
        docker_installed: false
      }

      // Make onSave call status callback with 'saving' and then hang
      mockOnSave.mockImplementation((_data, _info, onStatusChange) => {
        onStatusChange?.('saving')
        return new Promise(() => {}) // Never resolves
      })

      const { useServerForm } = await import('@/hooks/useServerForm')
      vi.mocked(useServerForm).mockReturnValue({
        formData: {
          name: 'Test Server',
          host: '192.168.1.100',
          port: 22,
          username: 'admin',
          auth_type: 'password',
          credentials: {
            password: 'secret123',
            private_key: '',
            passphrase: ''
          }
        },
        handleInputChange: mockHandleInputChange,
        handleAuthTypeChange: mockHandleAuthTypeChange,
        handleCredentialChange: mockHandleCredentialChange,
        resetForm: mockResetForm
      })

      render(
        <ServerFormDialog
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          server={existingServer}
          title="Edit Server"
        />
      )

      await user.click(screen.getByRole('button', { name: /save/i }))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled()
      })
    })
  })

  describe('host:port parsing', () => {
    it('should parse port from host input when colon is included', async () => {
      const user = userEvent.setup()

      render(
        <ServerFormDialog
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          title="Add Server"
        />
      )

      const hostInput = screen.getByRole('textbox', { name: /^Host/ })
      await user.type(hostInput, '192.168.1.100:2222')

      // Should call handleInputChange for both host and port
      expect(mockHandleInputChange).toHaveBeenCalled()
    })
  })

  describe('accessibility', () => {
    it('should have proper dialog role', () => {
      render(
        <ServerFormDialog
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          title="Add Server"
        />
      )

      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('should have labeled form fields', () => {
      render(
        <ServerFormDialog
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          title="Add Server"
        />
      )

      // All inputs should be accessible by role and name
      expect(screen.getByRole('textbox', { name: /^Name/ })).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /^Host/ })).toBeInTheDocument()
      expect(screen.getByRole('spinbutton', { name: /^Port/ })).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /^Username/ })).toBeInTheDocument()
    })
  })
})
