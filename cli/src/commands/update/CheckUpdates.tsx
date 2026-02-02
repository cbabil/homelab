import { Box, Text, useApp } from 'ink';
import React, { useState, useEffect } from 'react';
import { Banner, Spinner } from '../../components/ui/index.js';
import { ErrorDisplay, SuccessDisplay } from '../../components/common/index.js';
import { useMCP } from '../../hooks/useMCP.js';
import { checkForUpdates } from '../../lib/patch.js';
import { requireAdmin } from '../../lib/auth.js';

interface CheckUpdatesProps {
  options: {
    mcpUrl?: string;
  };
}

interface UpdateResult {
  success: boolean;
  components?: {
    backend: string;
    frontend: string;
    api: string;
  };
  latest_version?: string;
  update_available?: boolean;
  release_url?: string;
  error?: string;
}

type Step = 'init' | 'checking' | 'done' | 'error';

export function CheckUpdates({ options }: CheckUpdatesProps) {
  const { exit } = useApp();
  const { connected, connecting, error: mcpError } = useMCP(options.mcpUrl);

  const [step, setStep] = useState<Step>('init');
  const [result, setResult] = useState<UpdateResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Initialize and require auth
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
        setStep('checking');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Initialization failed');
        setStep('error');
      }
    };

    init();
  }, [connected, step]);

  // Check for updates
  useEffect(() => {
    if (step !== 'checking') return;

    const check = async () => {
      try {
        const updateResult = await checkForUpdates();
        if (updateResult.success) {
          setResult(updateResult);
          setStep('done');
        } else {
          setError(updateResult.error || 'Failed to check for updates');
          setStep('error');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Check failed');
        setStep('error');
      }
    };

    check();
  }, [step]);

  // Exit after completion
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

      {step === 'checking' && <Spinner text="Checking for updates..." />}

      {step === 'done' && result && (
        <Box flexDirection="column">
          <SuccessDisplay message="Update check complete" />

          <Box flexDirection="column" marginTop={1}>
            <Text color="cyan">Current versions:</Text>
            {result.components && (
              <Box flexDirection="column" marginLeft={2}>
                <Text color="gray">Backend:  {result.components.backend}</Text>
                <Text color="gray">Frontend: {result.components.frontend}</Text>
                <Text color="gray">API:      {result.components.api}</Text>
              </Box>
            )}
          </Box>

          {result.latest_version && (
            <Box marginTop={1}>
              <Text color="gray">Latest version: {result.latest_version}</Text>
            </Box>
          )}

          <Box marginTop={1}>
            {result.update_available ? (
              <Box flexDirection="column">
                <Text color="yellow">⚠ Update available!</Text>
                {result.release_url && (
                  <Text color="gray">  Release URL: {result.release_url}</Text>
                )}
              </Box>
            ) : (
              <Text color="green">✔ You are running the latest version</Text>
            )}
          </Box>
        </Box>
      )}

      {step === 'error' && <ErrorDisplay message={error || 'Unknown error'} />}
    </Box>
  );
}
