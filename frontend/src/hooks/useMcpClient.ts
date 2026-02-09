/**
 * MCP Client Hook
 *
 * React hook wrapper for the TomoMCPClient.
 * Designed specifically for FastMCP Streamable-HTTP transport.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useToast } from '@/components/ui/Toast';
import { TomoMCPClient } from '@/services/mcpClient';
import type { MCPResponse, MCPToolDefinition } from '@/types/mcp';

// MCP resource/prompt types (placeholder until full MCP spec implementation)
interface MCPResource {
  uri: string;
  name: string;
  description?: string;
  mimeType?: string;
}

interface MCPPrompt {
  name: string;
  description?: string;
  arguments?: Array<{ name: string; description?: string; required?: boolean }>;
}

interface UseMcpClientOptions {
  serverUrl: string;
  clientName?: string;
  autoReconnect?: boolean;
  transportType?: 'auto' | 'http' | 'sse';
}

interface UseMcpClientReturn {
  // Connection state
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;

  // MCP capabilities
  tools: MCPToolDefinition[];
  resources: MCPResource[];
  prompts: MCPPrompt[];

  // Actions
  callTool: <T>(name: string, params: Record<string, unknown>) => Promise<MCPResponse<T>>;
  readResource: (uri: string) => Promise<MCPResource>;
  getPrompt: (name: string, args?: Record<string, unknown>) => Promise<MCPPrompt>;
  authenticate: () => Promise<void>;
}

export function useMcpClient({
  serverUrl,
  autoReconnect = true,
}: UseMcpClientOptions): UseMcpClientReturn {
  const { addToast } = useToast();
  const clientRef = useRef<TomoMCPClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hasShownConnectionError = useRef(false);
  const hasShownConnectionSuccess = useRef(false);
  const isConnectedRef = useRef(false);
  const isConnectingRef = useRef(false);
  const retryCountRef = useRef(0);
  const maxRetries = 10;
  const baseDelayMs = 1000;
  const maxDelayMs = 60000;

  const handleConnectionSuccess = useCallback(() => {
    setIsConnected(true);
    setError(null);
    hasShownConnectionError.current = false;
    hasShownConnectionSuccess.current = true;
    retryCountRef.current = 0;
  }, []);

  const handleConnectionFailure = useCallback(
    (message: string) => {
      setError(message);
      setIsConnected(false);

      if (!hasShownConnectionError.current) {
        addToast({
          type: 'error',
          title: 'Connection Failed',
          message,
          duration: 4000,
        });
        hasShownConnectionError.current = true;
      }
    },
    [addToast]
  );

  // Initialize client
  useEffect(() => {
    clientRef.current = new TomoMCPClient(serverUrl);
  }, [serverUrl]);

  // Keep refs in sync with state
  isConnectedRef.current = isConnected;
  isConnectingRef.current = isConnecting;

  // Connection state management
  const connect = useCallback(async () => {
    if (!clientRef.current || isConnectingRef.current || isConnectedRef.current) return;

    setIsConnecting(true);
    setError(null);

    try {
      await clientRef.current.connect();
      handleConnectionSuccess();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Connection failed';
      handleConnectionFailure(errorMessage);
    } finally {
      setIsConnecting(false);
    }
  }, [handleConnectionFailure, handleConnectionSuccess]);

  // Auto-connect on mount - runs once
  useEffect(() => {
    let mounted = true;
    let hasAttempted = false;

    const attemptConnection = async () => {
      if (!clientRef.current || hasAttempted) return;
      hasAttempted = true;

      setIsConnecting(true);
      setError(null);

      try {
        await clientRef.current.connect();
        if (mounted) handleConnectionSuccess();
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Connection failed';
        if (mounted) handleConnectionFailure(errorMessage);
      } finally {
        if (mounted) setIsConnecting(false);
      }
    };

    attemptConnection();

    return () => {
      mounted = false;
    };
  }, [serverUrl]); // Only re-run if serverUrl changes

  // Reconnection logic with exponential backoff
  useEffect(() => {
    if (!autoReconnect || isConnected || isConnecting) return;
    if (retryCountRef.current >= maxRetries) return;

    const delay = Math.min(baseDelayMs * Math.pow(2, retryCountRef.current), maxDelayMs);
    retryCountRef.current += 1;

    const reconnectTimer = setTimeout(() => {
      connect();
    }, delay);

    return () => clearTimeout(reconnectTimer);
  }, [autoReconnect, isConnected, isConnecting, connect]);

  // Tool calling function
  const callTool = useCallback(
    async <T>(name: string, params: Record<string, unknown>): Promise<MCPResponse<T>> => {
      if (!clientRef.current) {
        return {
          success: false,
          error: 'MCP client not initialized',
          message: 'Tool execution failed',
        };
      }

      return await clientRef.current.callTool<T>(name, params);
    },
    []
  );

  // Placeholder functions for compatibility
  const readResource = useCallback(async (_uri: string) => {
    throw new Error('Resource reading not yet implemented');
  }, []);

  const getPrompt = useCallback(async (_name: string, _args?: Record<string, unknown>) => {
    throw new Error('Prompt retrieval not yet implemented');
  }, []);

  const authenticate = useCallback(async () => {
    // Authentication handled automatically in TomoMCPClient
    return connect();
  }, [connect]);

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
    authenticate,
  };
}
