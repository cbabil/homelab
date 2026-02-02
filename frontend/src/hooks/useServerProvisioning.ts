/** useServerProvisioning - State machine for server provisioning workflow */

import { useState, useCallback, useRef } from 'react'
import { ProvisioningState, ProvisioningStep, ProvisioningStepStatus } from '@/types/server'
import { useMCP } from '@/providers/MCPProvider'
import {
  TestConnectionResponse, InstallDockerResponse, InstallAgentResponse,
  INITIAL_STEPS, initialState, updateStep, extractError,
} from './provisioningHelpers'

export function useServerProvisioning() {
  const [state, setState] = useState<ProvisioningState>(initialState)
  const { client, isConnected } = useMCP()
  const stepStartTime = useRef<number>(0)
  const startTimer = () => { stepStartTime.current = Date.now() }
  const getElapsed = () => Date.now() - stepStartTime.current
  const errMsg = (e: unknown, fallback: string) => e instanceof Error ? e.message : fallback

  const setStep = useCallback((id: ProvisioningStep['id'], status: ProvisioningStepStatus, extras?: Partial<ProvisioningStep>) => {
    setState((prev) => ({ ...prev, steps: updateStep(prev.steps, id, { status, ...extras }) }))
  }, [])

  const startProvisioning = useCallback(async (serverId: string) => {
    if (!isConnected) return
    setState({ ...initialState, isProvisioning: true, serverId, steps: [...INITIAL_STEPS] })
    startTimer()
    setStep('connection', 'active', { message: 'Testing connection...' })
    try {
      const res = await client.callTool<TestConnectionResponse>('test_connection', { server_id: serverId })
      const duration = getElapsed()
      if (!res.data?.success) {
        setStep('connection', 'error', { error: extractError(res.data, 'Connection failed'), duration })
        setState((prev) => ({ ...prev, canRetry: true, currentStep: 'connection' }))
        return
      }
      const dockerInstalled = res.data.docker_installed ?? false
      const agentInstalled = res.data.agent_installed ?? false
      setStep('connection', 'success', { message: 'Connected successfully', duration })
      setState((prev) => ({ ...prev, dockerInstalled, currentStep: 'docker' }))
      if (!dockerInstalled) setState((prev) => ({ ...prev, requiresDecision: 'docker' }))
      else {
        setStep('docker', 'success', { message: 'Docker already installed' })
        if (agentInstalled) {
          setStep('agent', 'success', { message: 'Agent already installed' })
          setState((prev) => ({ ...prev, isProvisioning: false, currentStep: 'complete', requiresDecision: undefined }))
        } else {
          setState((prev) => ({ ...prev, currentStep: 'agent', requiresDecision: 'agent' }))
        }
      }
    } catch (e) {
      setStep('connection', 'error', { error: errMsg(e, 'Connection failed'), duration: getElapsed() })
      setState((prev) => ({ ...prev, canRetry: true }))
    }
  }, [client, isConnected, setStep])

  const installDocker = useCallback(async () => {
    if (!state.serverId || !isConnected) return
    startTimer()
    setStep('docker', 'active', { message: 'Installing Docker...' })
    setState((prev) => ({ ...prev, requiresDecision: undefined }))
    try {
      const res = await client.callTool<InstallDockerResponse>('install_docker', { server_id: state.serverId })
      if (!res.data?.success) {
        setStep('docker', 'error', { error: extractError(res.data, 'Docker installation failed'), duration: getElapsed() })
        setState((prev) => ({ ...prev, canRetry: true, requiresDecision: 'docker' }))
        return
      }
      setStep('docker', 'success', { message: 'Docker installed successfully', duration: getElapsed() })
      setState((prev) => ({ ...prev, dockerInstalled: true, currentStep: 'agent', requiresDecision: 'agent' }))
    } catch (e) {
      setStep('docker', 'error', { error: errMsg(e, 'Docker installation failed'), duration: getElapsed() })
      setState((prev) => ({ ...prev, canRetry: true, requiresDecision: 'docker' }))
    }
  }, [state.serverId, isConnected, client, setStep])

  const skipDocker = useCallback(() => {
    setStep('docker', 'skipped', { message: 'Docker installation skipped' })
    setState((prev) => ({ ...prev, requiresDecision: 'agent', currentStep: 'agent' }))
  }, [setStep])

  const installAgent = useCallback(async () => {
    if (!state.serverId || !isConnected) return
    startTimer()
    setStep('agent', 'active', { message: 'Installing agent...' })
    setState((prev) => ({ ...prev, requiresDecision: undefined }))
    try {
      const res = await client.callTool<InstallAgentResponse>('install_agent', { server_id: state.serverId })
      if (!res.data?.success) {
        setStep('agent', 'error', { error: extractError(res.data, 'Agent installation failed'), duration: getElapsed() })
        setState((prev) => ({ ...prev, canRetry: true, requiresDecision: 'agent' }))
        return
      }
      setStep('agent', 'success', { message: 'Agent installed successfully', duration: getElapsed() })
      setState((prev) => ({ ...prev, isProvisioning: false, currentStep: 'complete', requiresDecision: undefined }))
    } catch (e) {
      setStep('agent', 'error', { error: errMsg(e, 'Agent installation failed'), duration: getElapsed() })
      setState((prev) => ({ ...prev, canRetry: true, requiresDecision: 'agent' }))
    }
  }, [state.serverId, isConnected, client, setStep])

  const skipAgent = useCallback(() => {
    setStep('agent', 'skipped', { message: 'Agent installation skipped' })
    setState((prev) => ({ ...prev, isProvisioning: false, currentStep: 'complete', requiresDecision: undefined }))
  }, [setStep])

  const retry = useCallback(() => {
    if (!state.serverId) return
    const failed = state.steps.find((s) => s.status === 'error')
    if (!failed) return
    setState((prev) => ({ ...prev, canRetry: false }))
    if (failed.id === 'connection') startProvisioning(state.serverId)
    else if (failed.id === 'docker') installDocker()
    else if (failed.id === 'agent') installAgent()
  }, [state.serverId, state.steps, startProvisioning, installDocker, installAgent])

  const cancel = useCallback(async () => {
    if (state.serverId && isConnected) {
      try { await client.callTool('delete_server', { server_id: state.serverId }) } catch { /* cleanup */ }
    }
    setState(initialState)
  }, [state.serverId, isConnected, client])

  return { state, startProvisioning, installDocker, skipDocker, installAgent, skipAgent, retry, cancel, reset: useCallback(() => setState(initialState), []) }
}
