/**
 * MCP Provider
 * 
 * React context provider using the official use-mcp package.
 * Provides modern MCP client access throughout the application.
 */

import { createContext, useContext, ReactNode } from 'react'
import { useMcpClient } from '@/hooks/useMcpClient'
import type { MCPResponse } from '@/types/mcp'

interface MCPContextType {
  client: {
    callTool: <T>(name: string, params: Record<string, unknown>) => Promise<MCPResponse<T>>
    isConnected: () => boolean
  }
  isConnected: boolean
  error: string | null
}

const MCPContext = createContext<MCPContextType | null>(null)

interface MCPProviderProps {
  children: ReactNode
  serverUrl: string
  transportType?: 'auto' | 'http' | 'sse'
}

export function MCPProvider({ children, serverUrl, transportType = 'http' }: MCPProviderProps) {
  const mcpClient = useMcpClient({ 
    serverUrl,
    clientName: 'Homelab Assistant',
    autoReconnect: true,
    transportType
  })

  const contextValue: MCPContextType = {
    client: {
      callTool: mcpClient.callTool,
      isConnected: () => mcpClient.isConnected
    },
    isConnected: mcpClient.isConnected,
    error: mcpClient.error
  }

  return (
    <MCPContext.Provider value={contextValue}>
      {children}
    </MCPContext.Provider>
  )
}

export function useMCP(): MCPContextType {
  const context = useContext(MCPContext)
  if (!context) {
    throw new Error('useMCP must be used within an MCPProvider')
  }
  return context
}