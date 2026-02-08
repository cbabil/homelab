/**
 * Hook for the reset-password prompt flow.
 */

import { useState, useCallback, useRef } from 'react';
import { resetPassword } from '../lib/admin.js';
import { validatePassword } from '../lib/validation.js';
import type { ActivityEntry } from '../app/dashboard-types.js';

type ResetPwStep = 'password' | 'confirm' | null;

interface ResetPasswordFlowOptions {
  addActivity: (type: ActivityEntry['type'], message: string) => void;
  setInputValue: (value: string) => void;
  setRunning: (running: boolean) => void;
}

export function useResetPasswordFlow({
  addActivity,
  setInputValue,
  setRunning,
}: ResetPasswordFlowOptions) {
  const [step, setStep] = useState<ResetPwStep>(null);
  const [username, setUsername] = useState('');
  const passwordRef = useRef('');

  const startReset = useCallback((targetUsername: string) => {
    setUsername(targetUsername);
    setStep('password');
  }, []);

  const handleSubmit = useCallback(
    async (input: string) => {
      if (step === 'password') {
        const validation = validatePassword(input);
        if (!validation.valid) {
          addActivity('ERR', validation.error || 'Invalid password');
          setInputValue('');
          return;
        }
        passwordRef.current = input;
        setStep('confirm');
        setInputValue('');
        return;
      }

      if (step === 'confirm') {
        if (input !== passwordRef.current) {
          addActivity('ERR', 'Passwords do not match');
          setStep('password');
          passwordRef.current = '';
          setInputValue('');
          return;
        }

        // Copy password to local var and clear ref immediately
        const passwordCopy = passwordRef.current;
        passwordRef.current = '';

        setInputValue('');
        setRunning(true);
        addActivity('SYS', `Resetting password for ${username}...`);

        try {
          const result = await resetPassword(username, passwordCopy);
          if (result.success) {
            addActivity('OK', `Password reset for ${username}`);
          } else {
            addActivity('ERR', result.error || 'Failed to reset password');
          }
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'Failed to reset password';
          addActivity('ERR', msg);
        } finally {
          setRunning(false);
          setStep(null);
          setUsername('');
        }
      }
    },
    [step, username, addActivity, setInputValue, setRunning]
  );

  const promptLabel = step === 'password' ? 'New password: '
    : step === 'confirm' ? 'Confirm password: '
    : undefined;

  return {
    step,
    startReset,
    handleSubmit,
    promptLabel,
    promptMask: step !== null,
    isActive: step !== null,
  };
}
