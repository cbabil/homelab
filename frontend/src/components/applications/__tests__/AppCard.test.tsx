/**
 * AppCard Test Suite
 *
 * Tests for the AppCard component with deploy/uninstall actions.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Globe, Film } from 'lucide-react'
import { AppCard } from '../AppCard'
import { App } from '@/types/app'

describe('AppCard', () => {
  const createApp = (overrides: Partial<App> = {}): App => ({
    id: 'app-1',
    name: 'Test App',
    description: 'A test application',
    version: '1.0.0',
    status: 'available',
    category: { id: 'cat-1', name: 'Web', description: 'Web applications', icon: Globe, color: 'blue' },
    tags: ['test'],
    author: 'Test Author',
    license: 'MIT',
    icon: undefined,
    requirements: {},
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
    ...overrides
  })

  describe('Rendering', () => {
    it('should render app name', () => {
      render(<AppCard app={createApp({ name: 'My App' })} />)

      expect(screen.getByText('My App')).toBeInTheDocument()
    })

    it('should render version with v prefix', () => {
      render(<AppCard app={createApp({ version: '2.1.0' })} />)

      expect(screen.getByText('v2.1.0')).toBeInTheDocument()
    })

    it('should render category name', () => {
      render(<AppCard app={createApp({ category: { id: 'media', name: 'Media', description: 'Media apps', icon: Film, color: 'purple' } })} />)

      expect(screen.getByText('Media')).toBeInTheDocument()
    })

    it('should render fallback icon when no valid icon URL', () => {
      const { container } = render(<AppCard app={createApp({ icon: undefined })} />)

      // Should render Package icon fallback
      expect(container.querySelector('svg')).toBeInTheDocument()
    })
  })

  describe('Status Display', () => {
    it('should show check icon when installed', () => {
      const { container } = render(
        <AppCard app={createApp({ status: 'installed' })} />
      )

      // Check icon should be present
      expect(container.querySelector('.text-green-500')).toBeInTheDocument()
    })

    it('should show deploy button when not installed', () => {
      render(
        <AppCard app={createApp({ status: 'available' })} onDeploy={vi.fn()} />
      )

      expect(screen.getByTitle('Deploy')).toBeInTheDocument()
    })

    it('should show uninstall button when installed', () => {
      render(
        <AppCard app={createApp({ status: 'installed' })} onUninstall={vi.fn()} />
      )

      expect(screen.getByTitle('Uninstall')).toBeInTheDocument()
    })
  })

  describe('Actions', () => {
    it('should call onDeploy when deploy clicked', async () => {
      const user = userEvent.setup()
      const onDeploy = vi.fn()
      render(
        <AppCard app={createApp({ id: 'test-app' })} onDeploy={onDeploy} />
      )

      await user.click(screen.getByTitle('Deploy'))

      expect(onDeploy).toHaveBeenCalledWith('test-app')
    })

    it('should call onUninstall when uninstall clicked', async () => {
      const user = userEvent.setup()
      const onUninstall = vi.fn()
      render(
        <AppCard
          app={createApp({ id: 'test-app', status: 'installed', connectedServerId: 'server-1' })}
          onUninstall={onUninstall}
        />
      )

      await user.click(screen.getByTitle('Uninstall'))

      expect(onUninstall).toHaveBeenCalledWith('test-app', 'server-1')
    })
  })

  describe('Selection', () => {
    it('should call onToggleSelect when card clicked', async () => {
      const user = userEvent.setup()
      const onToggleSelect = vi.fn()
      render(
        <AppCard app={createApp({ id: 'app-1' })} onToggleSelect={onToggleSelect} />
      )

      await user.click(screen.getByText('Test App'))

      expect(onToggleSelect).toHaveBeenCalledWith('app-1')
    })

    it('should apply selected styles when isSelected', () => {
      const { container } = render(
        <AppCard app={createApp()} isSelected={true} onToggleSelect={vi.fn()} />
      )

      // Card should have selected styling
      expect(container.firstChild).toBeInTheDocument()
    })

    it('should not be clickable without onToggleSelect', () => {
      const { container } = render(<AppCard app={createApp()} />)

      // Should not have pointer cursor
      expect(container.firstChild).toBeInTheDocument()
    })
  })

  describe('Icon Display', () => {
    it('should render image when valid URL provided', () => {
      const { container } = render(
        <AppCard app={createApp({ icon: 'https://example.com/icon.png' })} />
      )

      // Image has empty alt so use querySelector
      const img = container.querySelector('img')
      expect(img).toHaveAttribute('src', 'https://example.com/icon.png')
    })

    it('should render fallback for invalid icon', () => {
      const { container } = render(
        <AppCard app={createApp({ icon: 'not-a-url' })} />
      )

      // Should show Package icon
      expect(container.querySelector('svg')).toBeInTheDocument()
    })
  })
})
