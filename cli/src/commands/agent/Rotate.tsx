import { Box, Text, useApp } from 'ink';
import React, { useState, useEffect } from 'react';
import { Banner, Spinner } from '../../components/ui/index.js';
import { ErrorDisplay } from '../../components/common/index.js';
import { useMCP } from '../../hooks/useMCP.js';
import { rotateAgentToken, RotateTokenData } from '../../lib/agent.js';
import { requireAdmin } from '../../lib/auth.js';

interface RotateProps {
  serverId: string;
  options: {
    mcpUrl?: string;
  };
}

type Step = 'init' | 'rotating' | 'done' | 'error';

export function Rotate({ serverId, options }: RotateProps) {
  const { exit } = useApp();
  const { connected, connecting, error: mcpError } = useMCP(options.mcpUrl);

  const [step, setStep] = useState<Step>('init');
  const [rotationData, setRotationData] = useState<RotateTokenData | null>(null);
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
        setStep('rotating');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Initialization failed');
        setStep('error');
      }
    };

    init();
  }, [connected, step]);

  useEffect(() => {
    if (step !== 'rotating') return;

    const rotate = async () => {
      try {
        const result = await rotateAgentToken(serverId);
        if (result.success && result.data) {
          setRotationData(result.data as unknown as RotateTokenData);
          setStep('done');
        } else {
          setError(result.error || `Failed to rotate token for server '${serverId}'`);
          setStep('error');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Token rotation failed');
        setStep('error');
      }
    };

    rotate();
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

  return (
    <Box flexDirection="column">
      <Banner />

      {connecting && <Spinner text="Connecting to server..." />}
      {step === 'init' && connected && <Spinner text="Authenticating..." />}
      {step === 'rotating' && <Spinner text="Rotating agent token..." />}

      {step === 'done' && rotationData && (
        <Box flexDirection="column">
          <Text color="green">Token rotation initiated successfully!</Text>
          <Box flexDirection="column" marginLeft={2} marginTop={1}>
            <Text color="gray">Agent ID: {rotationData.agent_id}</Text>
            <Text color="gray">Server ID: {rotationData.server_id}</Text>
            <Text color="gray">
              Grace Period: {rotationData.grace_period_seconds} seconds
            </Text>
            <Text color="gray">
              Token Expires: {rotationData.token_expires_at}
            </Text>
          </Box>
          <Box marginTop={1}>
            <Text color="cyan">
              The agent will receive the new token via WebSocket.
            </Text>
          </Box>
        </Box>
      )}

      {step === 'error' && <ErrorDisplay message={error || 'Unknown error'} />}
    </Box>
  );
}
