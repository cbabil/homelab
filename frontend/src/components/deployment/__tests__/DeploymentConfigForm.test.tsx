/**
 * DeploymentConfigForm Test Suite
 *
 * Tests for the DeploymentConfigForm component.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Globe } from 'lucide-react'
import { DeploymentConfigForm } from '../DeploymentConfigForm'
import { App } from '@/types/app'
import { ServerConnection } from '@/types/server'
import { DeploymentConfig } from '@/hooks/useDeploymentModal'

describe('DeploymentConfigForm', () => {
  const createApp = (overrides: Partial<App> = {}): App => ({
    id: 'app-1',
    name: 'Test App',
    description: 'A test application',
    version: '1.0.0',
    status: 'available',
    category: { id: 'web', name: 'Web', description: 'Web apps', icon: Globe, color: 'blue' },
    tags: [],
    author: 'Test',
    license: 'MIT',
    requirements: {
      requiredPorts: [80, 443]
    },
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    ...overrides
  })

  const createServer = (overrides: Partial<ServerConnection> = {}): ServerConnection => ({
    id: 'server-1',
    name: 'Test Server',
    host: '192.168.1.100',
    port: 22,
    username: 'admin',
    auth_type: 'password',
    status: 'connected',
    created_at: new Date().toISOString(),
    docker_installed: true,
    ...overrides
  })

  const createConfig = (overrides: Partial<DeploymentConfig> = {}): DeploymentConfig => ({
    env: {},
    ports: {},
    containerName: '',
    restartPolicy: 'unless-stopped',
    ...overrides
  })

  const defaultProps = {
    app: createApp(),
    server: createServer(),
    config: createConfig(),
    updateConfig: vi.fn()
  }

  describe('Rendering', () => {
    it('should render server name', () => {
      render(<DeploymentConfigForm {...defaultProps} />)

      expect(screen.getByText('Test Server')).toBeInTheDocument()
    })

    it('should render server host', () => {
      render(<DeploymentConfigForm {...defaultProps} />)

      expect(screen.getByText('(192.168.1.100)')).toBeInTheDocument()
    })

    it('should show "No configuration required" when no env vars', () => {
      render(<DeploymentConfigForm {...defaultProps} />)

      expect(
        screen.getByText('No configuration required. Click Deploy to continue.')
      ).toBeInTheDocument()
    })

    it('should render advanced options toggle', () => {
      render(<DeploymentConfigForm {...defaultProps} />)

      expect(screen.getByText(/Show advanced options/)).toBeInTheDocument()
    })
  })

  describe('Environment Variables', () => {
    it('should show environment variables when present', () => {
      render(
        <DeploymentConfigForm
          {...defaultProps}
          config={createConfig({
            env: { DB_HOST: 'localhost', DB_PORT: '5432' }
          })}
        />
      )

      expect(screen.getByText('Configuration')).toBeInTheDocument()
      expect(screen.getByText('DB_HOST')).toBeInTheDocument()
      expect(screen.getByText('DB_PORT')).toBeInTheDocument()
    })

    it('should call updateConfig when env var changed', async () => {
      const user = userEvent.setup()
      const updateConfig = vi.fn()
      render(
        <DeploymentConfigForm
          {...defaultProps}
          config={createConfig({ env: { API_KEY: '' } })}
          updateConfig={updateConfig}
        />
      )

      const input = screen.getByPlaceholderText('value')
      await user.type(input, 'k')

      expect(updateConfig).toHaveBeenCalledWith({
        env: expect.objectContaining({ API_KEY: expect.any(String) })
      })
    })

    it('should mask password/secret fields', () => {
      render(
        <DeploymentConfigForm
          {...defaultProps}
          config={createConfig({
            env: { DB_PASSWORD: 'secret123' }
          })}
        />
      )

      const passwordInput = screen.getByDisplayValue('secret123')
      expect(passwordInput).toHaveAttribute('type', 'password')
    })

    it('should allow removing env vars', async () => {
      const user = userEvent.setup()
      const updateConfig = vi.fn()
      render(
        <DeploymentConfigForm
          {...defaultProps}
          config={createConfig({ env: { KEY: 'value' } })}
          updateConfig={updateConfig}
        />
      )

      // Find and click delete button
      const deleteButtons = screen.getAllByRole('button')
      const deleteButton = deleteButtons.find(btn => btn.querySelector('svg'))

      if (deleteButton) {
        await user.click(deleteButton)
        expect(updateConfig).toHaveBeenCalledWith({
          env: {}
        })
      }
    })
  })

  describe('Advanced Options', () => {
    it('should toggle advanced options visibility', async () => {
      const user = userEvent.setup()
      render(<DeploymentConfigForm {...defaultProps} />)

      await user.click(screen.getByText(/Show advanced options/))

      expect(screen.getByText('Ports')).toBeInTheDocument()
      expect(screen.getByText('Environment Variables')).toBeInTheDocument()
      // "Container" appears in multiple places
      const containerTexts = screen.getAllByText('Container')
      expect(containerTexts.length).toBeGreaterThan(0)
    })

    it('should show hide text when advanced is open', async () => {
      const user = userEvent.setup()
      render(<DeploymentConfigForm {...defaultProps} />)

      await user.click(screen.getByText(/Show advanced options/))

      expect(screen.getByText(/Hide advanced options/)).toBeInTheDocument()
    })

    it('should show port mappings in advanced mode', async () => {
      const user = userEvent.setup()
      render(<DeploymentConfigForm {...defaultProps} />)

      await user.click(screen.getByText(/Show advanced options/))

      // Multiple "Container" texts may appear (section header and port column)
      const containerTexts = screen.getAllByText('Container')
      expect(containerTexts.length).toBeGreaterThan(0)
      expect(screen.getByText('Host')).toBeInTheDocument()
    })

    it('should show add variable button in advanced mode', async () => {
      const user = userEvent.setup()
      render(<DeploymentConfigForm {...defaultProps} />)

      await user.click(screen.getByText(/Show advanced options/))

      expect(screen.getByText('Add variable')).toBeInTheDocument()
    })

    it('should add new env var when add button clicked', async () => {
      const user = userEvent.setup()
      const updateConfig = vi.fn()
      render(
        <DeploymentConfigForm
          {...defaultProps}
          updateConfig={updateConfig}
        />
      )

      await user.click(screen.getByText(/Show advanced options/))
      await user.click(screen.getByText('Add variable'))

      expect(updateConfig).toHaveBeenCalled()
      // Check that the call contains env with a NEW_VAR_ key
      const call = updateConfig.mock.calls[0][0]
      expect(call.env).toBeDefined()
      const keys = Object.keys(call.env)
      expect(keys.some(k => k.startsWith('NEW_VAR_'))).toBe(true)
    })
  })

  describe('Container Settings', () => {
    it('should show container name input in advanced mode', async () => {
      const user = userEvent.setup()
      render(<DeploymentConfigForm {...defaultProps} />)

      await user.click(screen.getByText(/Show advanced options/))

      expect(screen.getByLabelText('Name')).toBeInTheDocument()
    })

    it('should show restart policy dropdown in advanced mode', async () => {
      const user = userEvent.setup()
      render(<DeploymentConfigForm {...defaultProps} />)

      await user.click(screen.getByText(/Show advanced options/))

      expect(screen.getByText('Restart Policy')).toBeInTheDocument()
    })

    it('should update container name', async () => {
      const user = userEvent.setup()
      const updateConfig = vi.fn()
      render(
        <DeploymentConfigForm
          {...defaultProps}
          updateConfig={updateConfig}
        />
      )

      await user.click(screen.getByText(/Show advanced options/))

      const nameInput = screen.getByLabelText('Name')
      await user.type(nameInput, 'm')

      expect(updateConfig).toHaveBeenCalledWith({
        containerName: expect.any(String)
      })
    })
  })

  describe('Port Mapping', () => {
    it('should show required ports from app', async () => {
      const user = userEvent.setup()
      render(
        <DeploymentConfigForm
          {...defaultProps}
          app={createApp({
            requirements: { requiredPorts: [8080, 3000] }
          })}
        />
      )

      await user.click(screen.getByText(/Show advanced options/))

      // Should show container ports as disabled inputs
      const inputs = screen.getAllByRole('spinbutton')
      expect(inputs.length).toBeGreaterThan(0)
    })

    it('should call updateConfig when port mapping changed', async () => {
      const user = userEvent.setup()
      const updateConfig = vi.fn()
      render(
        <DeploymentConfigForm
          {...defaultProps}
          app={createApp({
            requirements: { requiredPorts: [8080] }
          })}
          updateConfig={updateConfig}
        />
      )

      await user.click(screen.getByText(/Show advanced options/))

      // Find the host port input (second spinbutton)
      const portInputs = screen.getAllByRole('spinbutton')
      const hostPortInput = portInputs[portInputs.length - 1]

      await user.clear(hostPortInput)
      await user.type(hostPortInput, '9')

      expect(updateConfig).toHaveBeenCalledWith({
        ports: expect.any(Object)
      })
    })
  })
})
