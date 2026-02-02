/**
 * AuthenticationSection Test Suite
 *
 * Tests for the AuthenticationSection component that combines
 * authentication type selection with credential inputs.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthenticationSection } from '../AuthenticationSection'

// Mock child components to isolate testing
vi.mock('../PrivateKeyFileInput', () => ({
  PrivateKeyFileInput: ({ value, onChange, required }: { value: string, onChange: (v: string) => void, required: boolean }) => (
    <input
      data-testid="private-key-input"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      required={required}
    />
  )
}))

vi.mock('../ReadOnlyPrivateKeyDisplay', () => ({
  ReadOnlyPrivateKeyDisplay: ({ onUpdateKey }: { onUpdateKey: () => void }) => (
    <div data-testid="readonly-key-display">
      <button onClick={onUpdateKey}>Update Key</button>
    </div>
  )
}))

describe('AuthenticationSection', () => {
  const defaultProps = {
    authType: 'password' as const,
    credentials: {
      password: '',
      private_key: '',
      passphrase: ''
    },
    onAuthTypeChange: vi.fn(),
    onCredentialChange: vi.fn()
  }

  describe('Rendering', () => {
    it('should render auth type selector', () => {
      render(<AuthenticationSection {...defaultProps} />)

      expect(screen.getByText('Authentication')).toBeInTheDocument()
      expect(screen.getByLabelText('Password')).toBeInTheDocument()
      expect(screen.getByLabelText('Private Key')).toBeInTheDocument()
    })
  })

  describe('Password Auth Type', () => {
    it('should show password input when password auth selected', () => {
      render(<AuthenticationSection {...defaultProps} authType="password" />)

      expect(screen.getByPlaceholderText('Enter password')).toBeInTheDocument()
    })

    it('should call onCredentialChange when password typed', async () => {
      const user = userEvent.setup()
      const onCredentialChange = vi.fn()
      render(
        <AuthenticationSection
          {...defaultProps}
          authType="password"
          onCredentialChange={onCredentialChange}
        />
      )

      await user.type(screen.getByPlaceholderText('Enter password'), 'secret')

      expect(onCredentialChange).toHaveBeenCalledWith('password', expect.any(String))
    })
  })

  describe('Key Auth Type', () => {
    it('should show private key input when key auth selected', () => {
      render(<AuthenticationSection {...defaultProps} authType="key" />)

      expect(screen.getByTestId('private-key-input')).toBeInTheDocument()
    })

    it('should show passphrase input when key auth selected', () => {
      render(<AuthenticationSection {...defaultProps} authType="key" />)

      expect(screen.getByPlaceholderText('Key passphrase')).toBeInTheDocument()
    })

    it('should call onCredentialChange when passphrase typed', async () => {
      const user = userEvent.setup()
      const onCredentialChange = vi.fn()
      render(
        <AuthenticationSection
          {...defaultProps}
          authType="key"
          onCredentialChange={onCredentialChange}
        />
      )

      await user.type(screen.getByPlaceholderText('Key passphrase'), 'pass')

      expect(onCredentialChange).toHaveBeenCalledWith('passphrase', expect.any(String))
    })
  })

  describe('Edit Mode with Existing Key', () => {
    it('should show read-only display when editing with existing key', () => {
      render(
        <AuthenticationSection
          {...defaultProps}
          authType="key"
          credentials={{ private_key: '***EXISTING_KEY***' }}
          isEditMode={true}
        />
      )

      expect(screen.getByTestId('readonly-key-display')).toBeInTheDocument()
    })

    it('should show key input after clicking update', async () => {
      const user = userEvent.setup()
      render(
        <AuthenticationSection
          {...defaultProps}
          authType="key"
          credentials={{ private_key: '***EXISTING_KEY***' }}
          isEditMode={true}
        />
      )

      await user.click(screen.getByRole('button', { name: /update key/i }))

      expect(screen.getByTestId('private-key-input')).toBeInTheDocument()
    })
  })

  describe('Auth Type Change', () => {
    it('should call onAuthTypeChange when switching to key', async () => {
      const user = userEvent.setup()
      const onAuthTypeChange = vi.fn()
      render(
        <AuthenticationSection
          {...defaultProps}
          authType="password"
          onAuthTypeChange={onAuthTypeChange}
        />
      )

      await user.click(screen.getByLabelText('Private Key'))

      expect(onAuthTypeChange).toHaveBeenCalledWith('key')
    })

    it('should call onAuthTypeChange when switching to password', async () => {
      const user = userEvent.setup()
      const onAuthTypeChange = vi.fn()
      render(
        <AuthenticationSection
          {...defaultProps}
          authType="key"
          onAuthTypeChange={onAuthTypeChange}
        />
      )

      await user.click(screen.getByLabelText('Password'))

      expect(onAuthTypeChange).toHaveBeenCalledWith('password')
    })
  })
})
