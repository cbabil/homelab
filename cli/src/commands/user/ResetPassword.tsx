import { Box, useApp } from 'ink';
import React, { useState, useEffect } from 'react';
import { Banner, Spinner, TextInput, PasswordInput } from '../../components/ui/index.js';
import { ErrorDisplay, SuccessDisplay } from '../../components/common/index.js';
import { useMCP } from '../../hooks/useMCP.js';
import { resetPassword, getUser } from '../../lib/admin.js';
import { requireAdmin } from '../../lib/auth.js';

interface ResetPasswordProps {
  options: {
    username?: string;
    password?: string;
    mcpUrl?: string;
  };
}

type Step =
  | 'init'
  | 'username'
  | 'password'
  | 'confirmPassword'
  | 'resetting'
  | 'done'
  | 'error';

export function ResetPassword({ options }: ResetPasswordProps) {
  const { exit } = useApp();
  const { connected, connecting, error: mcpError } = useMCP(options.mcpUrl);

  const [step, setStep] = useState<Step>('init');
  const [username, setUsername] = useState(options.username || '');
  const [password, setPassword] = useState(options.password || '');
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

        if (options.username && options.password) {
          setStep('resetting');
        } else if (options.username) {
          setStep('password');
        } else {
          setStep('username');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Initialization failed');
        setStep('error');
      }
    };

    init();
  }, [connected, step, options.username, options.password]);

  // Handle password reset
  useEffect(() => {
    if (step !== 'resetting') return;

    const reset = async () => {
      try {
        const existing = await getUser(username);
        if (!existing) {
          setError(`User '${username}' not found`);
          setStep('error');
          return;
        }

        const result = await resetPassword(username, password);
        if (result.success) {
          setStep('done');
        } else {
          setError(result.error || 'Failed to reset password');
          setStep('error');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Reset failed');
        setStep('error');
      }
    };

    reset();
  }, [step, username, password]);

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

      {step === 'username' && (
        <TextInput
          label="Enter username"
          onSubmit={(value) => {
            setUsername(value);
            setStep('password');
          }}
          validate={(value) => (value.length >= 1 ? null : 'Username is required')}
        />
      )}

      {step === 'password' && (
        <PasswordInput
          label="Enter new password"
          onSubmit={(value) => {
            setPassword(value);
            setStep('confirmPassword');
          }}
          validate={(value) =>
            value.length >= 8 ? null : 'Password must be at least 8 characters'
          }
        />
      )}

      {step === 'confirmPassword' && (
        <PasswordInput
          label="Confirm new password"
          onSubmit={(value) => {
            if (value === password) {
              setStep('resetting');
            } else {
              setError('Passwords do not match');
              setStep('password');
            }
          }}
        />
      )}

      {step === 'resetting' && <Spinner text="Resetting password..." />}

      {step === 'done' && (
        <SuccessDisplay
          message="Password reset successfully"
          details={{ Username: username }}
        />
      )}

      {step === 'error' && <ErrorDisplay message={error || 'Unknown error'} />}
    </Box>
  );
}
