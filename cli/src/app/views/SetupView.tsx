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

type SetupStep = 'username' | 'password' | 'confirmPassword' | 'creating' | 'done' | 'error';

interface SetupViewProps {
  step: SetupStep;
  username: string;
  error: string | null;
}

function PasswordRequirements() {
  return (
    <Box flexDirection="column" marginTop={1}>
      <Text color={COLORS.dim}>{'Password requirements:'}</Text>
      <Text color={COLORS.dim}>{'  - At least 12 characters'}</Text>
      <Text color={COLORS.dim}>{'  - One uppercase letter'}</Text>
      <Text color={COLORS.dim}>{'  - One lowercase letter'}</Text>
      <Text color={COLORS.dim}>{'  - One number'}</Text>
      <Text color={COLORS.dim}>{'  - One special character'}</Text>
    </Box>
  );
}

export function SetupView({ step, username, error }: SetupViewProps) {
  return (
    <Panel title="INITIAL_SETUP">
      <Box flexDirection="column">
        <Text color={COLORS.bright} bold>
          {'Welcome to Tomo'}
        </Text>
        <Text color={COLORS.primary}>
          {'No admin account found. Create one to get started.'}
        </Text>

        <Box marginTop={1} flexDirection="column">
          {step === 'username' && (
            <Text color={COLORS.bright}>
              {'Step 1/3: Enter admin username (min 3 chars, alphanumeric)'}
            </Text>
          )}

          {step === 'password' && (
            <Box flexDirection="column">
              <Text color={COLORS.bright}>
                {`Step 2/3: Enter password for "${username}"`}
              </Text>
              <PasswordRequirements />
            </Box>
          )}

          {step === 'confirmPassword' && (
            <Text color={COLORS.bright}>
              {'Step 3/3: Confirm password'}
            </Text>
          )}

          {step === 'creating' && (
            <Text color={COLORS.dim}>
              {'Creating admin account...'}
            </Text>
          )}

          {step === 'done' && (
            <Text color={COLORS.bright} bold>
              {`Admin "${username}" created. You are now logged in.`}
            </Text>
          )}

          {step === 'error' && (
            <Text color={COLORS.error}>
              {`Setup failed: ${error || 'Unknown error'}`}
            </Text>
          )}
        </Box>
      </Box>
    </Panel>
  );
}
