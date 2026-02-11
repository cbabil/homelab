/**
 * Hook for the login prompt flow.
 */

import { useState, useCallback } from 'react';
import { authenticateAdmin } from '../lib/auth.js';
import type { ActivityEntry } from '../app/dashboard-types.js';
import { t } from '../i18n/index.js';

export type LoginStep = 'username' | 'password' | null;

interface LoginFlowOptions {
  addActivity: (type: ActivityEntry['type'], message: string) => void;
  onAuthenticated: (username: string) => void;
  setInputValue: (value: string) => void;
  setRunning: (running: boolean) => void;
}

export function useLoginFlow({
  addActivity,
  onAuthenticated,
  setInputValue,
  setRunning,
}: LoginFlowOptions) {
  const [loginStep, setLoginStep] = useState<LoginStep>(null);
  const [loginUsername, setLoginUsername] = useState('');

  const startLogin = useCallback(() => {
    setLoginStep('username');
  }, []);

  const handleSubmit = useCallback(
    async (input: string) => {
      if (loginStep === 'username') {
        if (!input.trim()) return;
        setLoginUsername(input.trim());
        setLoginStep('password');
        setInputValue('');
        return;
      }

      if (loginStep === 'password') {
        setInputValue('');
        setRunning(true);
        addActivity('SYS', t('auth.authenticating', { username: loginUsername }));
        try {
          const result = await authenticateAdmin(loginUsername, input);
          if (result.success) {
            setLoginStep(null);
            setRunning(false);
            onAuthenticated(loginUsername);
            addActivity('OK', t('auth.authenticated', { username: loginUsername }));
          } else {
            setRunning(false);
            addActivity('ERR', result.error || t('auth.authenticationFailed'));
            setLoginStep('username');
          }
        } catch (err) {
          setRunning(false);
          const msg = err instanceof Error ? err.message : t('auth.authenticationFailed');
          addActivity('ERR', msg);
          setLoginStep('username');
        }
        setLoginUsername('');
      }
    },
    [loginStep, loginUsername, addActivity, onAuthenticated, setInputValue, setRunning]
  );

  const promptLabel = loginStep === 'username' ? t('prompts.username')
    : loginStep === 'password' ? t('prompts.password')
    : undefined;

  const promptMask = loginStep === 'password';

  return {
    loginStep,
    startLogin,
    handleSubmit,
    promptLabel,
    promptMask,
    isActive: loginStep !== null,
  };
}
