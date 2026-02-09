/**
 * Hook for the initial admin setup prompt flow.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { createAdmin } from '../lib/admin.js';
import { validateUsername, validatePassword } from '../lib/validation.js';
import type { ActivityEntry } from '../app/dashboard-types.js';

export type SetupStep =
  | 'username'
  | 'password'
  | 'confirmPassword'
  | 'creating'
  | 'done'
  | 'error'
  | null;

interface SetupFlowOptions {
  addActivity: (type: ActivityEntry['type'], message: string) => void;
  onAuthenticated: (username: string) => void;
  setInputValue: (value: string) => void;
  setRunning: (running: boolean) => void;
}

export function useSetupFlow({
  addActivity,
  onAuthenticated,
  setInputValue,
  setRunning,
}: SetupFlowOptions) {
  const [setupStep, setSetupStep] = useState<SetupStep>(null);
  const [setupUsername, setSetupUsername] = useState('');
  const setupPasswordRef = useRef('');
  const [setupError, setSetupError] = useState<string | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => {
    if (timeoutRef.current !== null) clearTimeout(timeoutRef.current);
  }, []);

  const startSetup = useCallback(() => {
    setSetupStep('username');
  }, []);

  const handleSubmit = useCallback(
    async (input: string) => {
      if (setupStep === 'username') {
        const result = validateUsername(input);
        if (!result.valid) {
          addActivity('ERR', result.error || 'Invalid username');
          return;
        }
        setSetupUsername(input.trim());
        setSetupStep('password');
        setInputValue('');
        return;
      }

      if (setupStep === 'password') {
        const result = validatePassword(input);
        if (!result.valid) {
          addActivity('ERR', result.error || 'Invalid password');
          return;
        }
        setupPasswordRef.current = input;
        setSetupStep('confirmPassword');
        setInputValue('');
        return;
      }

      if (setupStep === 'confirmPassword') {
        if (input !== setupPasswordRef.current) {
          addActivity('ERR', 'Passwords do not match');
          setSetupStep('password');
          setupPasswordRef.current = '';
          setInputValue('');
          return;
        }

        setSetupStep('creating');
        setInputValue('');
        setRunning(true);
        addActivity('SYS', `Creating admin "${setupUsername}"...`);

        // Copy password to local var and clear ref immediately
        const passwordCopy = setupPasswordRef.current;
        setupPasswordRef.current = '';

        try {
          const result = await createAdmin(setupUsername, passwordCopy);
          if (result.success) {
            setSetupStep('done');
            setRunning(false);
            onAuthenticated(setupUsername);
            addActivity('OK', `Admin "${setupUsername}" created successfully`);
            addActivity('OK', `Authenticated as ${setupUsername}`);
            timeoutRef.current = setTimeout(() => {
              setSetupStep(null);
              setSetupUsername('');
            }, 2000);
          } else {
            setSetupError(result.error || 'Failed to create admin');
            setSetupStep('error');
            setRunning(false);
            addActivity('ERR', result.error || 'Failed to create admin');
            timeoutRef.current = setTimeout(() => {
              setSetupStep('username');
              setSetupUsername('');
              setSetupError(null);
            }, 3000);
          }
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'Setup failed';
          setSetupError(msg);
          setSetupStep('error');
          setRunning(false);
          addActivity('ERR', msg);
          timeoutRef.current = setTimeout(() => {
            setSetupStep('username');
            setSetupUsername('');
            setSetupError(null);
          }, 3000);
        }
      }
    },
    [setupStep, setupUsername, addActivity, onAuthenticated, setInputValue, setRunning]
  );

  const promptLabel = setupStep === 'username' ? 'Username: '
    : setupStep === 'password' ? 'Password: '
    : setupStep === 'confirmPassword' ? 'Confirm Password: '
    : undefined;

  const promptMask = setupStep === 'password' || setupStep === 'confirmPassword';

  const isDisabled = setupStep === 'creating' || setupStep === 'done' || setupStep === 'error';

  return {
    setupStep,
    setupUsername,
    setupError,
    startSetup,
    handleSubmit,
    promptLabel,
    promptMask,
    isActive: setupStep !== null,
    isDisabled,
  };
}
