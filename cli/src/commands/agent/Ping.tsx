import { Box, Text, useApp } from 'ink';
import React, { useState, useEffect } from 'react';
import { Banner, Spinner } from '../../components/ui/index.js';
import { ErrorDisplay } from '../../components/common/index.js';
import { useMCP } from '../../hooks/useMCP.js';
import { pingAgent } from '../../lib/agent.js';
import { requireAdmin } from '../../lib/auth.js';

interface PingProps {
  serverId: string;
  options: {
    timeout?: string;
    mcpUrl?: string;
  };
}

type Step = 'init' | 'pinging' | 'done' | 'error';

export function Ping({ serverId, options }: PingProps) {
  const { exit } = useApp();
  const { connected, connecting, error: mcpError } = useMCP(options.mcpUrl);

  const [step, setStep] = useState<Step>('init');
  const [latency, setLatency] = useState<number | null>(null);
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
        setStep('pinging');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Initialization failed');
        setStep('error');
      }
    };

    init();
  }, [connected, step]);

  useEffect(() => {
    if (step !== 'pinging') return;

    const doPing = async () => {
      try {
        const timeout = options.timeout ? parseFloat(options.timeout) : 5;
        const result = await pingAgent(serverId, timeout);
        if (result && result.responsive) {
          setLatency(result.latency_ms);
          setStep('done');
        } else {
          setError('Agent did not respond');
          setStep('error');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Ping failed');
        setStep('error');
      }
    };

    doPing();
  }, [step, serverId, options.timeout]);

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
      {step === 'pinging' && (
        <Spinner text={`Pinging agent on server '${serverId}'...`} />
      )}

      {step === 'done' && latency !== null && (
        <Box>
          <Text color="green">✔ Pong! </Text>
          <Text>Agent responded in {latency}ms</Text>
        </Box>
      )}

      {step === 'error' && <ErrorDisplay message={error || 'Unknown error'} />}
    </Box>
  );
}
