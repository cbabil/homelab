import { Box, useApp } from 'ink';
import React, { useState, useEffect } from 'react';
import { Banner, Spinner } from '../../components/ui/index.js';
import { ErrorDisplay, SuccessDisplay } from '../../components/common/index.js';
import { useMCP } from '../../hooks/useMCP.js';
import { installAgent } from '../../lib/agent.js';
import { requireAdmin } from '../../lib/auth.js';

interface InstallProps {
  serverId: string;
  options: {
    mcpUrl?: string;
  };
}

type Step = 'init' | 'installing' | 'done' | 'error';

export function Install({ serverId, options }: InstallProps) {
  const { exit } = useApp();
  const { connected, connecting, error: mcpError } = useMCP(options.mcpUrl);

  const [step, setStep] = useState<Step>('init');
  const [result, setResult] = useState<{ agent_id?: string; version?: string } | null>(null);
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
        setStep('installing');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Initialization failed');
        setStep('error');
      }
    };

    init();
  }, [connected, step]);

  useEffect(() => {
    if (step !== 'installing') return;

    const install = async () => {
      try {
        const installResult = await installAgent(serverId);
        if (installResult.success && installResult.data) {
          const data = installResult.data as { agent_id?: string; version?: string };
          setResult({
            agent_id: data.agent_id,
            version: data.version,
          });
          setStep('done');
        } else {
          setError(installResult.error || 'Failed to install agent');
          setStep('error');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Installation failed');
        setStep('error');
      }
    };

    install();
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
      {step === 'installing' && (
        <Spinner text={`Installing agent on server '${serverId}'...`} />
      )}

      {step === 'done' && result && (
        <SuccessDisplay
          message="Agent installed successfully"
          details={{
            'Agent ID': result.agent_id || 'N/A',
            ...(result.version && { Version: result.version }),
          }}
        />
      )}

      {step === 'error' && <ErrorDisplay message={error || 'Unknown error'} />}
    </Box>
  );
}
