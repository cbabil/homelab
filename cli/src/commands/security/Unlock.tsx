import { Box, useApp } from 'ink';
import React, { useState, useEffect } from 'react';
import { Banner, Spinner, TextInput } from '../../components/ui/index.js';
import { ErrorDisplay, SuccessDisplay } from '../../components/common/index.js';
import { useMCP } from '../../hooks/useMCP.js';
import { unlockAccount } from '../../lib/security.js';
import { requireAdmin } from '../../lib/auth.js';

interface UnlockProps {
  options: {
    lockId?: string;
    admin?: string;
    notes?: string;
    mcpUrl?: string;
  };
}

type Step = 'init' | 'lockId' | 'admin' | 'unlocking' | 'done' | 'error';

export function Unlock({ options }: UnlockProps) {
  const { exit } = useApp();
  const { connected, connecting, error: mcpError } = useMCP(options.mcpUrl);

  const [step, setStep] = useState<Step>('init');
  const [lockId, setLockId] = useState(options.lockId || '');
  const [adminUsername, setAdminUsername] = useState(options.admin || '');
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

        if (options.lockId && options.admin) {
          setStep('unlocking');
        } else if (options.lockId) {
          setStep('admin');
        } else {
          setStep('lockId');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Initialization failed');
        setStep('error');
      }
    };

    init();
  }, [connected, step, options.lockId, options.admin]);

  useEffect(() => {
    if (step !== 'unlocking') return;

    const unlock = async () => {
      try {
        const result = await unlockAccount(lockId, adminUsername, options.notes);
        if (result.success) {
          setStep('done');
        } else {
          setError(result.error || 'Failed to unlock account');
          setStep('error');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unlock failed');
        setStep('error');
      }
    };

    unlock();
  }, [step, lockId, adminUsername, options.notes]);

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

      {step === 'lockId' && (
        <TextInput
          label="Enter lock ID"
          onSubmit={(value) => {
            setLockId(value);
            setStep('admin');
          }}
          validate={(value) => (value.length >= 1 ? null : 'Lock ID is required')}
        />
      )}

      {step === 'admin' && (
        <TextInput
          label="Enter admin username"
          onSubmit={(value) => {
            setAdminUsername(value);
            setStep('unlocking');
          }}
          validate={(value) => (value.length >= 1 ? null : 'Admin username is required')}
        />
      )}

      {step === 'unlocking' && <Spinner text="Unlocking account..." />}

      {step === 'done' && (
        <SuccessDisplay
          message="Account unlocked successfully"
          details={{ 'Lock ID': lockId }}
        />
      )}

      {step === 'error' && <ErrorDisplay message={error || 'Unknown error'} />}
    </Box>
  );
}
