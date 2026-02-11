/**
 * Initial system setup view.
 *
 * Shown when no admin user exists. Guides the user through
 * creating the first admin account.
 */

import { Box, Text } from 'ink';
import React from 'react';
import { COLORS } from '../theme.js';
import { Panel } from '../../components/dashboard/Panel.js';
import { t } from '../../i18n/index.js';

type SetupStep = 'username' | 'password' | 'confirmPassword' | 'creating' | 'done' | 'error';

interface SetupViewProps {
  step: SetupStep;
  username: string;
  error: string | null;
}

function PasswordRequirements() {
  return (
    <Box flexDirection="column" marginTop={1}>
      <Text color={COLORS.dim}>{t('setup.passwordRequirements')}</Text>
      <Text color={COLORS.dim}>{t('setup.passwordMinLength')}</Text>
      <Text color={COLORS.dim}>{t('setup.passwordUppercase')}</Text>
      <Text color={COLORS.dim}>{t('setup.passwordLowercase')}</Text>
      <Text color={COLORS.dim}>{t('setup.passwordNumber')}</Text>
      <Text color={COLORS.dim}>{t('setup.passwordSpecialChar')}</Text>
    </Box>
  );
}

export function SetupView({ step, username, error }: SetupViewProps) {
  return (
    <Panel title={t('setup.title')}>
      <Box flexDirection="column">
        <Text color={COLORS.bright} bold>
          {t('setup.welcomeToTomo')}
        </Text>
        <Text color={COLORS.primary}>
          {t('setup.noAdminFound')}
        </Text>

        <Box marginTop={1} flexDirection="column">
          {step === 'username' && (
            <Text color={COLORS.bright}>
              {t('setup.step1Username')}
            </Text>
          )}

          {step === 'password' && (
            <Box flexDirection="column">
              <Text color={COLORS.bright}>
                {t('setup.step2Password', { username })}
              </Text>
              <PasswordRequirements />
            </Box>
          )}

          {step === 'confirmPassword' && (
            <Text color={COLORS.bright}>
              {t('setup.step3Confirm')}
            </Text>
          )}

          {step === 'creating' && (
            <Text color={COLORS.dim}>
              {t('setup.creatingAdmin')}
            </Text>
          )}

          {step === 'done' && (
            <Text color={COLORS.bright} bold>
              {t('setup.adminCreated', { username })}
            </Text>
          )}

          {step === 'error' && (
            <Text color={COLORS.error}>
              {t('setup.setupFailed', { error: error || t('common.unknownError') })}
            </Text>
          )}
        </Box>
      </Box>
    </Panel>
  );
}
