import { Box, Text, useApp } from 'ink';
import React, { useState, useEffect } from 'react';
import { Banner, Spinner } from '../../components/ui/index.js';
import { ErrorDisplay } from '../../components/common/index.js';
import { useMCP } from '../../hooks/useMCP.js';
import { getAgentStatus, AgentInfo } from '../../lib/agent.js';
import { requireAdmin } from '../../lib/auth.js';

interface StatusProps {
  serverId: string;
  options: {
    mcpUrl?: string;
  };
}

type Step = 'init' | 'fetching' | 'done' | 'error';

export function Status({ serverId, options }: StatusProps) {
  const { exit } = useApp();
  const { connected, connecting, error: mcpError } = useMCP(options.mcpUrl);

  const [step, setStep] = useState<Step>('init');
  const [agentStatus, setAgentStatus] = useState<AgentInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!connected || step !== 'init') return;

    const init = async () => {
      try {
        const isAdmin = await requireAdmin();
        if (!isAdmin) {
          setError('Admin authentication required');
          setStep('error');
          return;
        }
        setStep('fetching');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Initialization failed');
        setStep('error');
      }
    };

    init();
  }, [connected, step]);

  useEffect(() => {
    if (step !== 'fetching') return;

    const fetch = async () => {
      try {
        const result = await getAgentStatus(serverId);
        if (result) {
          setAgentStatus(result);
          setStep('done');
        } else {
          setError(`No agent found for server '${serverId}'`);
          setStep('error');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch status');
        setStep('error');
      }
    };

    fetch();
  }, [step, serverId]);

  useEffect(() => {
    if (step === 'done' || step === 'error') {
      const timer = setTimeout(() => exit(), 100);
      return () => clearTimeout(timer);
    }
  }, [step, exit]);

  if (mcpError) {
    return (
      <Box flexDirection="column">
        <Banner />
        <ErrorDisplay message="Failed to connect to MCP server" details={mcpError} />
      </Box>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'green';
      case 'disconnected':
        return 'yellow';
      default:
        return 'gray';
    }
  };

  return (
    <Box flexDirection="column">
      <Banner />

      {connecting && <Spinner text="Connecting to server..." />}
      {step === 'init' && connected && <Spinner text="Authenticating..." />}
      {step === 'fetching' && <Spinner text="Fetching agent status..." />}

      {step === 'done' && agentStatus && (
        <Box flexDirection="column">
          <Text color="cyan">Agent Status for server '{serverId}':</Text>
          <Box flexDirection="column" marginLeft={2} marginTop={1}>
            <Text color="gray">Agent ID: {agentStatus.id}</Text>
            <Text>
              Status:{' '}
              <Text color={getStatusColor(agentStatus.status)}>
                {agentStatus.status.toUpperCase()}
              </Text>
            </Text>
            <Text color="gray">
              Connected: {agentStatus.is_connected ? 'Yes' : 'No'}
            </Text>
            <Text color="gray">Version: {agentStatus.version || 'unknown'}</Text>
            <Text color="gray">Last Seen: {agentStatus.last_seen || 'never'}</Text>
            <Text color="gray">
              Registered: {agentStatus.registered_at || 'pending'}
            </Text>
          </Box>
        </Box>
      )}

      {step === 'error' && <ErrorDisplay message={error || 'Unknown error'} />}
    </Box>
  );
}
