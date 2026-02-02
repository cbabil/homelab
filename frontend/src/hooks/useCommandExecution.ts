/**
 * useCommandExecution Hook
 *
 * Custom hook for executing commands on servers via MCP.
 * Supports routed execution (agent-first with SSH fallback).
 */

import { useState, useCallback } from 'react'
import { useMCP } from '@/providers/MCPProvider'
import type { CommandResult, ExecutionMethodsInfo, ExecutionMethod } from '@/types/server'

interface ExecuteOptions {
  timeout?: number
  forceSSH?: boolean
  forceAgent?: boolean
}

interface UseCommandExecutionReturn {
  isExecuting: boolean
  lastResult: CommandResult | null
  executeCommand: (
    serverId: string,
    command: string,
    options?: ExecuteOptions
  ) => Promise<CommandResult | null>
  getExecutionMethods: (serverId: string) => Promise<ExecutionMethodsInfo | null>
  clearResult: () => void
}

export function useCommandExecution(): UseCommandExecutionReturn {
  const [isExecuting, setIsExecuting] = useState(false)
  const [lastResult, setLastResult] = useState<CommandResult | null>(null)
  const { client, isConnected } = useMCP()

  const executeCommand = useCallback(
    async (
      serverId: string,
      command: string,
      options: ExecuteOptions = {}
    ): Promise<CommandResult | null> => {
      if (!isConnected) {
        console.error('MCP not connected')
        return null
      }

      setIsExecuting(true)
      try {
        const response = await client.callTool<{
          success: boolean
          data: {
            output: string
            method: ExecutionMethod
            exit_code?: number
            execution_time_ms?: number
          }
          message: string
          error?: string
        }>('execute_command', {
          server_id: serverId,
          command,
          timeout: options.timeout ?? 120,
          force_ssh: options.forceSSH ?? false,
          force_agent: options.forceAgent ?? false,
        })

        const result: CommandResult = {
          success: response.data?.success ?? false,
          output: response.data?.data?.output ?? '',
          method: response.data?.data?.method ?? 'none',
          exit_code: response.data?.data?.exit_code,
          execution_time_ms: response.data?.data?.execution_time_ms,
          error: response.data?.error ?? response.data?.message,
        }

        setLastResult(result)
        return result
      } catch (error) {
        console.error(`Failed to execute command on ${serverId}:`, error)
        const errorResult: CommandResult = {
          success: false,
          output: '',
          method: 'none',
          error: error instanceof Error ? error.message : 'Unknown error',
        }
        setLastResult(errorResult)
        return errorResult
      } finally {
        setIsExecuting(false)
      }
    },
    [client, isConnected]
  )

  const getExecutionMethods = useCallback(
    async (serverId: string): Promise<ExecutionMethodsInfo | null> => {
      if (!isConnected) return null

      try {
        const response = await client.callTool<{
          success: boolean
          data: ExecutionMethodsInfo
          message: string
        }>('get_execution_methods', { server_id: serverId })

        return response.data?.success ? response.data.data : null
      } catch (error) {
        console.error(`Failed to get execution methods for ${serverId}:`, error)
        return null
      }
    },
    [client, isConnected]
  )

  const clearResult = useCallback(() => {
    setLastResult(null)
  }, [])

  return {
    isExecuting,
    lastResult,
    executeCommand,
    getExecutionMethods,
    clearResult,
  }
}
