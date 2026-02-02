import { Box, Text, useApp } from 'ink';
import React, { useState, useEffect } from 'react';
import { Banner, Spinner } from '../../components/ui/index.js';
import { ErrorDisplay } from '../../components/common/index.js';
import { useMCP } from '../../hooks/useMCP.js';
import { listAgents, AgentInfo } from '../../lib/agent.js';
import { requireAdmin } from '../../lib/auth.js';

interface ListProps {
  options: {
    mcpUrl?: string;
  };
}

type Step = 'init' | 'fetching' | 'done' | 'error';

export function List({ options }: ListProps) {
  const { exit } = useApp();
  const { connected, connecting, error: mcpError } = useMCP(options.mcpUrl);

  const [step, setStep] = useState<Step>('init');
  const [agents, setAgents] = useState<AgentInfo[]>([]);
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
        const result = await listAgents();
        setAgents(result);
        setStep('done');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch agents');
        setStep('error');
      }
    };

    fetch();
  }, [step]);

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
      {step === 'fetching' && <Spinner text="Fetching agents..." />}

      {step === 'done' && agents.length === 0 && (
        <Text color="yellow">No agents found.</Text>
      )}

      {step === 'done' && agents.length > 0 && (
        <Box flexDirection="column">
          <Text color="cyan">Found {agents.length} agent(s):</Text>
          <Text color="gray">{'─'.repeat(80)}</Text>

          {agents.map((agent) => (
            <Box key={agent.id} flexDirection="column" marginBottom={1}>
              <Text>Agent ID: {agent.id}</Text>
              <Text color="gray">  Server ID: {agent.server_id}</Text>
              <Text>
                {'  Status: '}
                <Text color={getStatusColor(agent.status)}>
                  {agent.status.toUpperCase()}
                </Text>
              </Text>
              <Text color="gray">  Version: {agent.version || 'unknown'}</Text>
              <Text color="gray">  Last Seen: {agent.last_seen || 'never'}</Text>
              <Text color="gray">  Registered: {agent.registered_at || 'pending'}</Text>
              <Text color="gray">{'─'.repeat(80)}</Text>
            </Box>
          ))}
        </Box>
      )}

      {step === 'error' && <ErrorDisplay message={error || 'Unknown error'} />}
    </Box>
  );
}
