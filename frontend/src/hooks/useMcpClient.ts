/**
 * MCP Client Hook
 * 
 * React hook wrapper for the HomelabMCPClient.
 * Designed specifically for FastMCP Streamable-HTTP transport.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { useToast } from '@/components/ui/Toast'
import { HomelabMCPClient } from '@/services/mcpClient'
import type { MCPResponse } from '@/types/mcp'

interface UseMcpClientOptions {
  serverUrl: string
  clientName?: string
  autoReconnect?: boolean
  transportType?: 'auto' | 'http' | 'sse'
}

interface UseMcpClientReturn {
  // Connection state
  isConnected: boolean
  isConnecting: boolean
  error: string | null
  
  // MCP capabilities  
  tools: any[]
  resources: any[]
  prompts: any[]
  
  // Actions
  callTool: <T>(name: string, params: Record<string, unknown>) => Promise<MCPResponse<T>>
  readResource: (uri: string) => Promise<any>
  getPrompt: (name: string, args?: Record<string, unknown>) => Promise<any>
  authenticate: () => Promise<void>
}

export function useMcpClient({ 
  serverUrl, 
  clientName = 'Homelab Assistant',
  autoReconnect = true,
  transportType = 'http'
}: UseMcpClientOptions): UseMcpClientReturn {
  const { addToast } = useToast()
  const clientRef = useRef<HomelabMCPClient | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const hasShownConnectionError = useRef(false)

  const handleConnectionSuccess = useCallback(() => {
    setIsConnected(true)
    setError(null)
    hasShownConnectionError.current = false
    addToast({
      type: 'success',
      title: 'Connected',
      message: 'Successfully connected to homelab server.',
      duration: 3000
    })
  }, [addToast])

  const handleConnectionFailure = useCallback((message: string) => {
    setError(message)
    setIsConnected(false)

    if (!hasShownConnectionError.current) {
      addToast({
        type: 'error',
        title: 'Connection Failed',
        message,
        duration: 4000
      })
      hasShownConnectionError.current = true
    }
  }, [addToast])

  // Initialize client
  useEffect(() => {
    clientRef.current = new HomelabMCPClient(serverUrl)
  }, [serverUrl])

  // Connection state management
  const connect = useCallback(async () => {
    if (!clientRef.current || isConnecting || isConnected) return
    
    setIsConnecting(true)
    setError(null)
    
    try {
      await clientRef.current.connect()
      handleConnectionSuccess()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Connection failed'
      handleConnectionFailure(errorMessage)
    } finally {
      setIsConnecting(false)
    }
  }, [handleConnectionFailure, handleConnectionSuccess, isConnecting, isConnected])

  // Auto-connect on mount - immediate attempt
  useEffect(() => {
    const attemptConnection = async () => {
      if (!clientRef.current || isConnecting || isConnected) return
      
      setIsConnecting(true)
      setError(null)
      
      try {
        await clientRef.current.connect()
        handleConnectionSuccess()
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Connection failed'
        handleConnectionFailure(errorMessage)
      } finally {
        setIsConnecting(false)
      }
    }
    
    // Try connecting immediately
    attemptConnection()
    
    // Also try after a delay to ensure client is ready
    const timer = setTimeout(attemptConnection, 1000)
    return () => clearTimeout(timer)
  }, [handleConnectionFailure, handleConnectionSuccess])

  // Reconnection logic
  useEffect(() => {
    if (!autoReconnect || isConnected || isConnecting) return
    
    const reconnectTimer = setTimeout(() => {
      connect()
    }, 5000) // Retry every 5 seconds
    
    return () => clearTimeout(reconnectTimer)
  }, [autoReconnect, isConnected, isConnecting, connect])

  // Tool calling function
  const callTool = useCallback(async <T>(
    name: string, 
    params: Record<string, unknown>
  ): Promise<MCPResponse<T>> => {
    if (!clientRef.current) {
      return {
        success: false,
        error: 'MCP client not initialized',
        message: 'Tool execution failed'
      }
    }
    
    return await clientRef.current.callTool<T>(name, params)
  }, [])

  // Placeholder functions for compatibility
  const readResource = useCallback(async (uri: string) => {
    throw new Error('Resource reading not yet implemented')
  }, [])

  const getPrompt = useCallback(async (name: string, args?: Record<string, unknown>) => {
    throw new Error('Prompt retrieval not yet implemented')
  }, [])

  const authenticate = useCallback(async () => {
    // Authentication handled automatically in HomelabMCPClient
    return connect()
  }, [connect])

  return {
    isConnected,
    isConnecting,
    error,
    tools: [], // Tools discovery not yet implemented
    resources: [], // Resources discovery not yet implemented
    prompts: [], // Prompts discovery not yet implemented
    callTool,
    readResource,
    getPrompt,
    authenticate
  }
}
