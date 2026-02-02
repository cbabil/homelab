import { Box, useApp } from 'ink';
import React, { useState, useEffect } from 'react';
import { Banner, Spinner, TextInput, PasswordInput } from '../../components/ui/index.js';
import { ErrorDisplay, SuccessDisplay } from '../../components/common/index.js';
import { useMCP } from '../../hooks/useMCP.js';
import { exportBackup } from '../../lib/backup.js';
import { requireAdmin } from '../../lib/auth.js';

interface ExportProps {
  options: {
    output?: string;
    password?: string;
    mcpUrl?: string;
  };
}

type Step = 'init' | 'output' | 'password' | 'confirmPassword' | 'exporting' | 'done' | 'error';

export function Export({ options }: ExportProps) {
  const { exit } = useApp();
  const { connected, connecting, error: mcpError } = useMCP(options.mcpUrl);

  const [step, setStep] = useState<Step>('init');
  const [outputPath, setOutputPath] = useState(options.output || '');
  const [password, setPassword] = useState(options.password || '');
  const [result, setResult] = useState<{ path?: string; checksum?: string } | null>(null);
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

        if (options.output && options.password) {
          setStep('exporting');
        } else if (options.output) {
          setStep('password');
        } else {
          setStep('output');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Initialization failed');
        setStep('error');
      }
    };

    init();
  }, [connected, step, options.output, options.password]);

  useEffect(() => {
    if (step !== 'exporting') return;

    const doExport = async () => {
      try {
        const exportResult = await exportBackup(outputPath, password);
        if (exportResult.success) {
          setResult({ path: exportResult.path, checksum: exportResult.checksum });
          setStep('done');
        } else {
          setError(exportResult.error || 'Failed to export backup');
          setStep('error');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Export failed');
        setStep('error');
      }
    };

    doExport();
  }, [step, outputPath, password]);

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

      {step === 'output' && (
        <TextInput
          label="Enter output file path"
          onSubmit={(value) => {
            setOutputPath(value);
            setStep('password');
          }}
          validate={(value) => (value.length >= 1 ? null : 'Output path is required')}
        />
      )}

      {step === 'password' && (
        <PasswordInput
          label="Enter encryption password"
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
              setStep('exporting');
            } else {
              setError('Passwords do not match');
              setStep('password');
            }
          }}
        />
      )}

      {step === 'exporting' && <Spinner text="Exporting backup..." />}

      {step === 'done' && result && (
        <SuccessDisplay
          message="Backup exported successfully"
          details={{
            Path: result.path || outputPath,
            Checksum: result.checksum || 'N/A',
          }}
        />
      )}

      {step === 'error' && <ErrorDisplay message={error || 'Unknown error'} />}
    </Box>
  );
}
