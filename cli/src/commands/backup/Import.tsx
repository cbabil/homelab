import { Box, useApp } from 'ink';
import React, { useState, useEffect } from 'react';
import { Banner, Spinner, TextInput, PasswordInput } from '../../components/ui/index.js';
import { ErrorDisplay, SuccessDisplay } from '../../components/common/index.js';
import { useMCP } from '../../hooks/useMCP.js';
import { importBackup } from '../../lib/backup.js';
import { requireAdmin } from '../../lib/auth.js';

interface ImportProps {
  options: {
    input?: string;
    password?: string;
    overwrite?: boolean;
    mcpUrl?: string;
  };
}

type Step = 'init' | 'input' | 'password' | 'importing' | 'done' | 'error';

interface ImportResult {
  users_imported?: number;
  servers_imported?: number;
  apps_imported?: number;
}

export function Import({ options }: ImportProps) {
  const { exit } = useApp();
  const { connected, connecting, error: mcpError } = useMCP(options.mcpUrl);

  const [step, setStep] = useState<Step>('init');
  const [inputPath, setInputPath] = useState(options.input || '');
  const [password, setPassword] = useState(options.password || '');
  const [result, setResult] = useState<ImportResult | null>(null);
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

        if (options.input && options.password) {
          setStep('importing');
        } else if (options.input) {
          setStep('password');
        } else {
          setStep('input');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Initialization failed');
        setStep('error');
      }
    };

    init();
  }, [connected, step, options.input, options.password]);

  useEffect(() => {
    if (step !== 'importing') return;

    const doImport = async () => {
      try {
        const importResult = await importBackup(
          inputPath,
          password,
          options.overwrite || false
        );
        if (importResult.success) {
          setResult({
            users_imported: importResult.users_imported,
            servers_imported: importResult.servers_imported,
            apps_imported: importResult.apps_imported,
          });
          setStep('done');
        } else {
          setError(importResult.error || 'Failed to import backup');
          setStep('error');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Import failed');
        setStep('error');
      }
    };

    doImport();
  }, [step, inputPath, password, options.overwrite]);

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

      {step === 'input' && (
        <TextInput
          label="Enter input file path"
          onSubmit={(value) => {
            setInputPath(value);
            setStep('password');
          }}
          validate={(value) => (value.length >= 1 ? null : 'Input path is required')}
        />
      )}

      {step === 'password' && (
        <PasswordInput
          label="Enter decryption password"
          onSubmit={(value) => {
            setPassword(value);
            setStep('importing');
          }}
          validate={(value) => (value.length >= 1 ? null : 'Password is required')}
        />
      )}

      {step === 'importing' && <Spinner text="Importing backup..." />}

      {step === 'done' && result && (
        <SuccessDisplay
          message="Backup imported successfully"
          details={{
            'Users imported': String(result.users_imported ?? 0),
            'Servers imported': String(result.servers_imported ?? 0),
            ...(result.apps_imported !== undefined && {
              'Apps imported': String(result.apps_imported),
            }),
          }}
        />
      )}

      {step === 'error' && <ErrorDisplay message={error || 'Unknown error'} />}
    </Box>
  );
}
