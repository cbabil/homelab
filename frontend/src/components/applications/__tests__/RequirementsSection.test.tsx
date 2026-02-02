/**
 * RequirementsSection Test Suite
 *
 * Tests for the RequirementsSection form component.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { RequirementsSection } from '../RequirementsSection'
import { AppRequirements } from '@/types/app'

describe('RequirementsSection', () => {
  const defaultRequirements: AppRequirements = {}

  const defaultProps = {
    requirements: defaultRequirements,
    onChange: vi.fn()
  }

  describe('Rendering', () => {
    it('should render section title', () => {
      render(<RequirementsSection {...defaultProps} />)

      expect(screen.getByText('System Requirements')).toBeInTheDocument()
    })

    it('should render min RAM field', () => {
      render(<RequirementsSection {...defaultProps} />)

      expect(screen.getByText('Min RAM')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('512MB, 1GB, 2GB')).toBeInTheDocument()
    })

    it('should render min storage field', () => {
      render(<RequirementsSection {...defaultProps} />)

      expect(screen.getByText('Min Storage')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('100MB, 1GB, 10GB')).toBeInTheDocument()
    })

    it('should render required ports field', () => {
      render(<RequirementsSection {...defaultProps} />)

      expect(screen.getByText('Required Ports')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('80, 443, 8080')).toBeInTheDocument()
    })

    it('should render supported architectures field', () => {
      render(<RequirementsSection {...defaultProps} />)

      expect(screen.getByText('Supported Architectures')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('amd64, arm64, armv7')).toBeInTheDocument()
    })

    it('should render dependencies field', () => {
      render(<RequirementsSection {...defaultProps} />)

      expect(screen.getByText('Dependencies')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('docker, postgresql, redis')).toBeInTheDocument()
    })

    it('should show helper text for comma-separated fields', () => {
      render(<RequirementsSection {...defaultProps} />)

      expect(screen.getByText('Separate ports with commas')).toBeInTheDocument()
      expect(screen.getByText('Separate architectures with commas')).toBeInTheDocument()
      expect(screen.getByText('Separate dependencies with commas')).toBeInTheDocument()
    })
  })

  describe('Display Values', () => {
    it('should display current requirements values', () => {
      render(
        <RequirementsSection
          {...defaultProps}
          requirements={{
            minRam: '1GB',
            minStorage: '5GB',
            requiredPorts: [80, 443],
            supportedArchitectures: ['amd64', 'arm64'],
            dependencies: ['docker', 'redis']
          }}
        />
      )

      expect(screen.getByDisplayValue('1GB')).toBeInTheDocument()
      expect(screen.getByDisplayValue('5GB')).toBeInTheDocument()
      expect(screen.getByDisplayValue('80, 443')).toBeInTheDocument()
      expect(screen.getByDisplayValue('amd64, arm64')).toBeInTheDocument()
      expect(screen.getByDisplayValue('docker, redis')).toBeInTheDocument()
    })
  })

  describe('User Input', () => {
    it('should call onChange when min RAM changes', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<RequirementsSection {...defaultProps} onChange={onChange} />)

      await user.type(screen.getByPlaceholderText('512MB, 1GB, 2GB'), '2GB')

      expect(onChange).toHaveBeenCalledWith('minRam', expect.any(String))
    })

    it('should call onChange when min storage changes', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<RequirementsSection {...defaultProps} onChange={onChange} />)

      await user.type(screen.getByPlaceholderText('100MB, 1GB, 10GB'), '10GB')

      expect(onChange).toHaveBeenCalledWith('minStorage', expect.any(String))
    })

    it('should parse ports as number array', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<RequirementsSection {...defaultProps} onChange={onChange} />)

      await user.type(screen.getByPlaceholderText('80, 443, 8080'), '8')

      // Should have called with parsed number array
      expect(onChange).toHaveBeenCalledWith('requiredPorts', [8])
    })

    it('should parse architectures as string array', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<RequirementsSection {...defaultProps} onChange={onChange} />)

      await user.type(screen.getByPlaceholderText('amd64, arm64, armv7'), 'amd64, arm64')

      expect(onChange).toHaveBeenCalledWith('supportedArchitectures', expect.any(Array))
    })

    it('should parse dependencies as string array', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<RequirementsSection {...defaultProps} onChange={onChange} />)

      await user.type(screen.getByPlaceholderText('docker, postgresql, redis'), 'docker, redis')

      expect(onChange).toHaveBeenCalledWith('dependencies', expect.any(Array))
    })
  })

  describe('Port Parsing', () => {
    it('should filter out invalid port values', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<RequirementsSection {...defaultProps} onChange={onChange} />)

      // Type a letter which should result in empty array (NaN filtered out)
      await user.type(screen.getByPlaceholderText('80, 443, 8080'), 'a')

      // Should have called with empty array since 'a' is not a valid port
      expect(onChange).toHaveBeenCalledWith('requiredPorts', [])
    })
  })
})
