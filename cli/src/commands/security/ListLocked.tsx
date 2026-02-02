import { Box, Text, useApp } from 'ink';
import React, { useState, useEffect } from 'react';
import { Banner, Spinner } from '../../components/ui/index.js';
import { ErrorDisplay } from '../../components/common/index.js';
import { useMCP } from '../../hooks/useMCP.js';
import { getLockedAccounts, LockedAccount } from '../../lib/security.js';
import { requireAdmin } from '../../lib/auth.js';

interface ListLockedProps {
  options: {
    includeExpired?: boolean;
    includeUnlocked?: boolean;
    mcpUrl?: string;
  };
}

type Step = 'init' | 'fetching' | 'done' | 'error';

export function ListLocked({ options }: ListLockedProps) {
  const { exit } = useApp();
  const { connected, connecting, error: mcpError } = useMCP(options.mcpUrl);

  const [step, setStep] = useState<Step>('init');
  const [accounts, setAccounts] = useState<LockedAccount[]>([]);
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
        const result = await getLockedAccounts(
          options.includeExpired || false,
          options.includeUnlocked || false
        );
        setAccounts(result);
        setStep('done');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch accounts');
        setStep('error');
      }
    };

    fetch();
  }, [step, options.includeExpired, options.includeUnlocked]);

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
      {step === 'fetching' && <Spinner text="Fetching locked accounts..." />}

      {step === 'done' && accounts.length === 0 && (
        <Text color="green">✔ No locked accounts found.</Text>
      )}

      {step === 'done' && accounts.length > 0 && (
        <Box flexDirection="column">
          <Text color="cyan">Found {accounts.length} locked account(s):</Text>
          <Text color="gray">{'─'.repeat(80)}</Text>

          {accounts.map((account) => (
            <Box key={account.id} flexDirection="column" marginBottom={1}>
              <Text>ID: {account.id}</Text>
              <Text color="gray">  Type: {account.identifier_type.toUpperCase()}</Text>
              <Text color="gray">  Identifier: {account.identifier}</Text>
              <Text>
                {'  Status: '}
                <Text color={account.unlocked_at ? 'green' : 'red'}>
                  {account.unlocked_at ? 'UNLOCKED' : 'LOCKED'}
                </Text>
              </Text>
              <Text color="gray">  Failed Attempts: {account.attempt_count}</Text>
              <Text color="gray">  Locked At: {account.locked_at}</Text>
              <Text color="gray">  Expires: {account.lock_expires_at || 'permanent'}</Text>
              <Text color="gray">  IP Address: {account.ip_address}</Text>
              {account.unlocked_at && (
                <>
                  <Text color="gray">  Unlocked At: {account.unlocked_at}</Text>
                  <Text color="gray">  Unlocked By: {account.unlocked_by || 'unknown'}</Text>
                </>
              )}
              <Text color="gray">{'─'.repeat(80)}</Text>
            </Box>
          ))}
        </Box>
      )}

      {step === 'error' && <ErrorDisplay message={error || 'Unknown error'} />}
    </Box>
  );
}
