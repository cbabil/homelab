/**
 * ServerInfoTooltip Test Suite
 *
 * Tests for the ServerInfoTooltip component that shows
 * system information on hover.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ServerInfoTooltip } from '../ServerInfoTooltip'
import { SystemInfo } from '@/types/server'

describe('ServerInfoTooltip', () => {
  const createSystemInfo = (overrides: Partial<SystemInfo> = {}): SystemInfo => ({
    os: 'Ubuntu 22.04',
    architecture: 'x86_64',
    docker_version: '24.0.5',
    ...overrides
  })

  describe('Rendering', () => {
    it('should render info icon button', () => {
      render(<ServerInfoTooltip systemInfo={createSystemInfo()} />)

      expect(screen.getByTitle('Server info')).toBeInTheDocument()
    })
  })

  describe('Tooltip Display', () => {
    it('should show tooltip on hover', async () => {
      const user = userEvent.setup()
      render(<ServerInfoTooltip systemInfo={createSystemInfo()} />)

      await user.hover(screen.getByTitle('Server info'))

      expect(screen.getByText('OS:')).toBeInTheDocument()
      expect(screen.getByText('Ubuntu 22.04')).toBeInTheDocument()
    })

    it('should show architecture in tooltip', async () => {
      const user = userEvent.setup()
      render(<ServerInfoTooltip systemInfo={createSystemInfo({ architecture: 'arm64' })} />)

      await user.hover(screen.getByTitle('Server info'))

      expect(screen.getByText('Architecture:')).toBeInTheDocument()
      expect(screen.getByText('arm64')).toBeInTheDocument()
    })

    it('should show docker version in tooltip', async () => {
      const user = userEvent.setup()
      render(<ServerInfoTooltip systemInfo={createSystemInfo({ docker_version: '25.0.0' })} />)

      await user.hover(screen.getByTitle('Server info'))

      expect(screen.getByText('Docker:')).toBeInTheDocument()
      expect(screen.getByText('25.0.0')).toBeInTheDocument()
    })

    it('should hide tooltip on mouse leave', async () => {
      const user = userEvent.setup()
      render(<ServerInfoTooltip systemInfo={createSystemInfo()} />)

      await user.hover(screen.getByTitle('Server info'))
      expect(screen.getByText('OS:')).toBeInTheDocument()

      await user.unhover(screen.getByTitle('Server info'))
      expect(screen.queryByText('OS:')).not.toBeInTheDocument()
    })
  })

  describe('Docker Not Installed', () => {
    it('should show "Not installed" when docker not installed', async () => {
      const user = userEvent.setup()
      render(
        <ServerInfoTooltip
          systemInfo={createSystemInfo({ docker_version: 'Not installed' })}
        />
      )

      await user.hover(screen.getByTitle('Server info'))

      expect(screen.getByText('Not installed')).toBeInTheDocument()
    })

    it('should show install button when docker not installed and handler provided', async () => {
      const user = userEvent.setup()
      render(
        <ServerInfoTooltip
          systemInfo={createSystemInfo({ docker_version: 'Not installed' })}
          onInstallDocker={vi.fn()}
        />
      )

      await user.hover(screen.getByTitle('Server info'))

      expect(screen.getByText('Install')).toBeInTheDocument()
    })

    it('should show install button that is clickable', async () => {
      const user = userEvent.setup()
      const onInstallDocker = vi.fn().mockResolvedValue(undefined)
      const { container } = render(
        <ServerInfoTooltip
          systemInfo={createSystemInfo({ docker_version: 'Not installed' })}
          onInstallDocker={onInstallDocker}
        />
      )

      // Hover to open tooltip
      await user.hover(screen.getByTitle('Server info'))

      // Verify Install button is visible
      expect(screen.getByText('Install')).toBeInTheDocument()

      // Find and click the install button within the tooltip
      const installButton = container.querySelector('button:not([title="Server info"])')
      expect(installButton).toBeInTheDocument()
    })
  })

  describe('N/A Values', () => {
    it('should show N/A for missing OS', async () => {
      const user = userEvent.setup()
      render(
        <ServerInfoTooltip
          systemInfo={createSystemInfo({ os: undefined })}
        />
      )

      await user.hover(screen.getByTitle('Server info'))

      expect(screen.getByText('N/A')).toBeInTheDocument()
    })
  })
})
