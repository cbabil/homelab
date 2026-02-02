/**
 * RestoreOptionsPanel Test Suite
 *
 * Tests for the RestoreOptionsPanel component.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { RestoreOptionsPanel } from '../RestoreOptionsPanel'
import { RestoreOptions } from '@/services/tomoBackupService'

describe('RestoreOptionsPanel', () => {
  const defaultOptions: RestoreOptions = {
    includeSettings: true,
    includeServers: true,
    includeApplications: true,
    overwriteExisting: false
  }

  const defaultProps = {
    options: defaultOptions,
    onChange: vi.fn()
  }

  describe('Rendering', () => {
    it('should render import options title', () => {
      render(<RestoreOptionsPanel {...defaultProps} />)

      expect(screen.getByText('Import Options')).toBeInTheDocument()
    })

    it('should render settings checkbox', () => {
      render(<RestoreOptionsPanel {...defaultProps} />)

      expect(screen.getByText('Settings')).toBeInTheDocument()
    })

    it('should render servers checkbox', () => {
      render(<RestoreOptionsPanel {...defaultProps} />)

      expect(screen.getByText('Servers')).toBeInTheDocument()
    })

    it('should render apps checkbox', () => {
      render(<RestoreOptionsPanel {...defaultProps} />)

      expect(screen.getByText('Apps')).toBeInTheDocument()
    })

    it('should render overwrite checkbox', () => {
      render(<RestoreOptionsPanel {...defaultProps} />)

      expect(screen.getByText('Overwrite')).toBeInTheDocument()
    })

    it('should render description text', () => {
      render(<RestoreOptionsPanel {...defaultProps} />)

      expect(
        screen.getByText('Select what to restore and whether to overwrite existing data')
      ).toBeInTheDocument()
    })
  })

  describe('Checkbox States', () => {
    it('should check settings when includeSettings is true', () => {
      render(
        <RestoreOptionsPanel
          {...defaultProps}
          options={{ ...defaultOptions, includeSettings: true }}
        />
      )

      const checkboxes = screen.getAllByRole('checkbox')
      expect(checkboxes[0]).toBeChecked()
    })

    it('should uncheck settings when includeSettings is false', () => {
      render(
        <RestoreOptionsPanel
          {...defaultProps}
          options={{ ...defaultOptions, includeSettings: false }}
        />
      )

      const checkboxes = screen.getAllByRole('checkbox')
      expect(checkboxes[0]).not.toBeChecked()
    })

    it('should check servers when includeServers is true', () => {
      render(
        <RestoreOptionsPanel
          {...defaultProps}
          options={{ ...defaultOptions, includeServers: true }}
        />
      )

      const checkboxes = screen.getAllByRole('checkbox')
      expect(checkboxes[1]).toBeChecked()
    })

    it('should check apps when includeApplications is true', () => {
      render(
        <RestoreOptionsPanel
          {...defaultProps}
          options={{ ...defaultOptions, includeApplications: true }}
        />
      )

      const checkboxes = screen.getAllByRole('checkbox')
      expect(checkboxes[2]).toBeChecked()
    })

    it('should check overwrite when overwriteExisting is true', () => {
      render(
        <RestoreOptionsPanel
          {...defaultProps}
          options={{ ...defaultOptions, overwriteExisting: true }}
        />
      )

      const checkboxes = screen.getAllByRole('checkbox')
      expect(checkboxes[3]).toBeChecked()
    })
  })

  describe('User Interactions', () => {
    it('should call onChange when settings checkbox toggled', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<RestoreOptionsPanel {...defaultProps} onChange={onChange} />)

      const checkboxes = screen.getAllByRole('checkbox')
      await user.click(checkboxes[0])

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ includeSettings: false })
      )
    })

    it('should call onChange when servers checkbox toggled', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<RestoreOptionsPanel {...defaultProps} onChange={onChange} />)

      const checkboxes = screen.getAllByRole('checkbox')
      await user.click(checkboxes[1])

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ includeServers: false })
      )
    })

    it('should call onChange when apps checkbox toggled', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<RestoreOptionsPanel {...defaultProps} onChange={onChange} />)

      const checkboxes = screen.getAllByRole('checkbox')
      await user.click(checkboxes[2])

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ includeApplications: false })
      )
    })

    it('should call onChange when overwrite checkbox toggled', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<RestoreOptionsPanel {...defaultProps} onChange={onChange} />)

      const checkboxes = screen.getAllByRole('checkbox')
      await user.click(checkboxes[3])

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ overwriteExisting: true })
      )
    })

    it('should preserve other options when toggling one', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<RestoreOptionsPanel {...defaultProps} onChange={onChange} />)

      const checkboxes = screen.getAllByRole('checkbox')
      await user.click(checkboxes[0])

      expect(onChange).toHaveBeenCalledWith({
        includeSettings: false,
        includeServers: true,
        includeApplications: true,
        overwriteExisting: false
      })
    })
  })
})
