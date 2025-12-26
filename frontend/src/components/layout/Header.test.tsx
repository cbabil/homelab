/**
 * Unit tests for Header Component
 * 
 * Tests header rendering with MCP connection status.
 * Covers connected and disconnected states with proper context.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Header } from './Header'
import { useMCP } from '@/providers/MCPProvider'
import { ThemeProvider } from '@/providers/ThemeProvider'
import { MCPClient } from '@/types/mcp'

// Mock the MCP provider hook
vi.mock('@/providers/MCPProvider', async () => {
  const actual = await vi.importActual('@/providers/MCPProvider') as any
  return {
    ...actual,
    useMCP: vi.fn()
  }
})

const mockUseMCP = vi.mocked(useMCP)
const mockClient = {} as MCPClient

const renderHeaderWithProviders = () => render(
  <ThemeProvider><Header /></ThemeProvider>
)

describe('Header Component', () => {
  it('should render title and connected status', () => {
    mockUseMCP.mockReturnValue({ client: mockClient, isConnected: true, error: null })
    
    renderHeaderWithProviders()
    
    expect(screen.getByText('Homelab Assistant')).toBeInTheDocument()
    expect(screen.getByText('Professional Edition')).toBeInTheDocument()
    expect(screen.getByText('Connected')).toBeInTheDocument()
    
    const statusElement = screen.getByText('Connected').parentElement
    expect(statusElement?.querySelector('svg')).toBeInTheDocument()
  })

  it('should show disconnected status when MCP is disconnected', () => {
    mockUseMCP.mockReturnValue({
      client: mockClient, isConnected: false, error: 'Connection failed'
    })

    renderHeaderWithProviders()
    expect(screen.getByText('Disconnected')).toBeInTheDocument()
  })

  it('should have proper header structure', () => {
    mockUseMCP.mockReturnValue({ client: mockClient, isConnected: true, error: null })
    renderHeaderWithProviders()

    const header = screen.getByRole('banner')
    expect(header).toHaveClass('sticky', 'top-0', 'z-50')
  })

  it('should handle MCP provider context errors', () => {
    mockUseMCP.mockImplementation(() => {
      throw new Error('useMCP must be used within an MCPProvider')
    })

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => renderHeaderWithProviders())
      .toThrow('useMCP must be used within an MCPProvider')

    consoleSpy.mockRestore()
  })
})