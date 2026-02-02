import { Box, useApp } from 'ink';
import React, { useState, useEffect } from 'react';
import { Banner, Spinner, TextInput, PasswordInput } from '../../components/ui/index.js';
import { ErrorDisplay, SuccessDisplay } from '../../components/common/index.js';
import { useMCP } from '../../hooks/useMCP.js';
import { createAdmin, getUser } from '../../lib/admin.js';
import { checkSystemSetup, requireAdmin } from '../../lib/auth.js';

interface CreateAdminProps {
  options: {
    username?: string;
    password?: string;
    mcpUrl?: string;
  };
}

type Step =
  | 'init'
  | 'auth'
  | 'username'
  | 'password'
  | 'confirmPassword'
  | 'creating'
  | 'done'
  | 'error';

export function CreateAdmin({ options }: CreateAdminProps) {
  const { exit } = useApp();
  const { connected, connecting, error: mcpError } = useMCP(options.mcpUrl);

  const [step, setStep] = useState<Step>('init');
  const [username, setUsername] = useState(options.username || '');
  const [password, setPassword] = useState(options.password || '');
  const [error, setError] = useState<string | null>(null);

  // Initialize and check auth
  useEffect(() => {
    if (!connected || step !== 'init') return;

    const init = async () => {
      try {
        const needsSetup = await checkSystemSetup();
        if (!needsSetup) {
          const isAdmin = await requireAdmin();
          if (!isAdmin) {
            setError('Admin authentication required');
            setStep('error');
            return;
          }
        }

        // Determine starting step based on provided options
        if (options.username && options.password) {
          setStep('creating');
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

  // Handle create admin
  useEffect(() => {
    if (step !== 'creating') return;

    const create = async () => {
      try {
        // Check if user exists
        const existing = await getUser(username);
        if (existing) {
          setError(`User '${username}' already exists`);
          setStep('error');
          return;
        }

        const result = await createAdmin(username, password);
        if (result.success) {
          setStep('done');
        } else {
          setError(result.error || 'Failed to create admin');
          setStep('error');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Creation failed');
        setStep('error');
      }
    };

    create();
  }, [step, username, password]);

  // Exit after completion
  useEffect(() => {
    if (step === 'done' || step === 'error') {
      const timer = setTimeout(() => exit(), 100);
      return () => clearTimeout(timer);
    }
  }, [step, exit]);

  // Handle MCP errors
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

      {step === 'init' && connected && <Spinner text="Initializing..." />}

      {step === 'username' && (
        <TextInput
          label="Enter admin username"
          onSubmit={(value) => {
            setUsername(value);
            setStep('password');
          }}
          validate={(value) =>
            value.length >= 3 ? null : 'Username must be at least 3 characters'
          }
        />
      )}

      {step === 'password' && (
        <PasswordInput
          label="Enter admin password"
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
          label="Confirm password"
          onSubmit={(value) => {
            if (value === password) {
              setStep('creating');
            } else {
              setError('Passwords do not match');
              setStep('password');
            }
          }}
        />
      )}

      {step === 'creating' && <Spinner text="Creating admin user..." />}

      {step === 'done' && (
        <SuccessDisplay
          message="Admin user created successfully"
          details={{ Username: username }}
        />
      )}

      {step === 'error' && <ErrorDisplay message={error || 'Unknown error'} />}
    </Box>
  );
}
