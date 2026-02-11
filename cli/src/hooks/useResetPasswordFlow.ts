/**
 * Hook for the reset-password prompt flow.
 */

import { useState, useCallback, useRef } from 'react';
import { resetPassword } from '../lib/admin.js';
import { validatePassword } from '../lib/validation.js';
import type { ActivityEntry } from '../app/dashboard-types.js';
import { t } from '../i18n/index.js';

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
          addActivity('ERR', validation.error || t('validation.invalidPassword'));
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
          addActivity('ERR', t('validation.passwordsDoNotMatch'));
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
        addActivity('SYS', t('users.resettingPassword', { username }));

        try {
          const result = await resetPassword(username, passwordCopy);
          if (result.success) {
            addActivity('OK', t('users.passwordResetSuccess', { username }));
          } else {
            addActivity('ERR', result.error || t('users.failedToResetPassword'));
          }
        } catch (err) {
          const msg = err instanceof Error ? err.message : t('users.failedToResetPassword');
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

  const promptLabel = step === 'password' ? t('prompts.newPassword')
    : step === 'confirm' ? t('prompts.confirmNewPassword')
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
