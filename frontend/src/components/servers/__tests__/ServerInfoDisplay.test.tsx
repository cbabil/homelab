/**
 * Server Info Display Component Tests
 * 
 * Tests for server system information display component.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ServerInfoDisplay } from '../ServerInfoDisplay'
import { SystemInfo } from '@/types/server'

const mockSystemInfo: SystemInfo = {
  os: 'Ubuntu 22.04',
  kernel: '5.15.0-91-generic',
  architecture: 'x86_64',
  uptime: '15 days, 8:32',
  docker_version: '24.0.7'
}

describe('ServerInfoDisplay', () => {
  describe('when status is preparing', () => {
    it('should show loading state', () => {
      render(
        <ServerInfoDisplay 
          status="preparing" 
          systemInfo={undefined}
        />
      )
      
      expect(screen.getByText('Loading...')).toBeInTheDocument()
      expect(document.querySelector('.animate-spin')).toBeInTheDocument()
    })
  })

  describe('when status is error or disconnected without system info', () => {
    it('should show error state for error status', () => {
      render(
        <ServerInfoDisplay 
          status="error" 
          systemInfo={undefined}
        />
      )
      
      expect(screen.getByText('Info unavailable')).toBeInTheDocument()
    })

    it('should show error state for disconnected status', () => {
      render(
        <ServerInfoDisplay 
          status="disconnected" 
          systemInfo={undefined}
        />
      )
      
      expect(screen.getByText('Info unavailable')).toBeInTheDocument()
    })
  })

  describe('when system info is not available and status is connected', () => {
    it('should render nothing', () => {
      const { container } = render(
        <ServerInfoDisplay 
          status="connected" 
          systemInfo={undefined}
        />
      )
      
      expect(container.firstChild).toBeNull()
    })
  })

  describe('when system info is available', () => {
    it('should display all system information', () => {
      render(
        <ServerInfoDisplay 
          status="connected" 
          systemInfo={mockSystemInfo}
        />
      )
      
      // The compact version doesn't have a header title
      expect(screen.getByText('Ubuntu 22.04')).toBeInTheDocument()
      expect(screen.getByText('x86_64')).toBeInTheDocument()
      expect(screen.getByText('15 days, 8:32')).toBeInTheDocument()
      expect(screen.getByText('24.0.7')).toBeInTheDocument()
      // Kernel version is not shown in compact version
    })

    it('should format simple uptime correctly', () => {
      const systemInfoWithSimpleUptime: SystemInfo = {
        ...mockSystemInfo,
        uptime: '8:32'
      }
      
      render(
        <ServerInfoDisplay 
          status="connected" 
          systemInfo={systemInfoWithSimpleUptime}
        />
      )
      
      expect(screen.getByText('8h 32m')).toBeInTheDocument()
    })

    it('should handle zero minutes uptime', () => {
      const systemInfoWithZeroMinutes: SystemInfo = {
        ...mockSystemInfo,
        uptime: '8:00'
      }
      
      render(
        <ServerInfoDisplay 
          status="connected" 
          systemInfo={systemInfoWithZeroMinutes}
        />
      )
      
      expect(screen.getByText('8h')).toBeInTheDocument()
    })

    it('should handle zero hours uptime', () => {
      const systemInfoWithZeroHours: SystemInfo = {
        ...mockSystemInfo,
        uptime: '0:32'
      }
      
      render(
        <ServerInfoDisplay 
          status="connected" 
          systemInfo={systemInfoWithZeroHours}
        />
      )
      
      expect(screen.getByText('32m')).toBeInTheDocument()
    })

    it('should not show Docker version when not available', () => {
      const systemInfoWithoutDocker: SystemInfo = {
        os: 'Ubuntu 22.04',
        kernel: '5.15.0-91-generic',
        architecture: 'x86_64',
        uptime: '15 days, 8:32'
      }
      
      render(
        <ServerInfoDisplay 
          status="connected" 
          systemInfo={systemInfoWithoutDocker}
        />
      )
      
      expect(screen.getByText('Docker not installed')).toBeInTheDocument()
    })

    it('should apply custom className', () => {
      const { container } = render(
        <ServerInfoDisplay 
          status="connected" 
          systemInfo={mockSystemInfo}
          className="custom-class"
        />
      )
      
      expect(container.firstChild).toHaveClass('custom-class')
    })
  })

  describe('label display', () => {
    it('should show correct labels for each field', () => {
      render(
        <ServerInfoDisplay 
          status="connected" 
          systemInfo={mockSystemInfo}
        />
      )
      
      expect(screen.getByText('OS')).toBeInTheDocument()
      expect(screen.getByText('Arch')).toBeInTheDocument()
      expect(screen.getByText('Uptime')).toBeInTheDocument()
      expect(screen.getByText('Docker')).toBeInTheDocument()
    })
  })
})