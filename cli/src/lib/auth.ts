/**
 * CLI Authentication module
 *
 * Handles admin authentication for CLI commands.
 * Most CLI commands require admin privileges.
 */

import { getMCPClient } from './mcp-client.js';
import inquirer from 'inquirer';
import chalk from 'chalk';

interface LoginResponse {
  token: string;
  user: {
    id: string;
    username: string;
    role: string;
  };
}

interface SystemSetupResponse {
  needs_setup: boolean;
  is_setup: boolean;
}

interface AuthState {
  token: string | null;
  username: string | null;
  role: string | null;
}

// In-memory auth state for the CLI session
let authState: AuthState = {
  token: null,
  username: null,
  role: null
};

/**
 * Check if the system needs initial setup (no admin exists)
 */
export async function checkSystemSetup(): Promise<boolean> {
  const client = getMCPClient();
  const response = await client.callTool<SystemSetupResponse>('get_system_setup', {});

  if (response.success && response.data) {
    return response.data.needs_setup;
  }

  return false;
}

/**
 * Prompt for admin credentials and authenticate
 */
export async function authenticateAdmin(): Promise<boolean> {
  const answers = await inquirer.prompt([
    {
      type: 'input',
      name: 'username',
      message: chalk.cyan('?') + ' Admin username:',
      validate: (input: string) => input.length >= 1 || 'Username is required'
    },
    {
      type: 'password',
      name: 'password',
      message: chalk.cyan('?') + ' Admin password:',
      mask: '*',
      validate: (input: string) => input.length >= 1 || 'Password is required'
    }
  ]);

  const client = getMCPClient();
  const response = await client.callTool<LoginResponse>('login', {
    username: answers.username,
    password: answers.password
  });

  if (response.success && response.data) {
    const { token, user } = response.data;

    if (user.role !== 'admin') {
      console.log(chalk.red('\n✗ Error:') + ' Only admin users can run CLI commands');
      return false;
    }

    authState = {
      token,
      username: user.username,
      role: user.role
    };

    return true;
  }

  console.log(chalk.red('\n✗ Error:') + ' Invalid credentials');
  return false;
}

/**
 * Require admin authentication before running a command
 * Returns true if authenticated as admin, false otherwise
 */
export async function requireAdmin(): Promise<boolean> {
  // Check if system needs setup - if so, allow without auth
  const needsSetup = await checkSystemSetup();
  if (needsSetup) {
    return true; // Allow initial setup without auth
  }

  console.log(chalk.yellow('\nAdmin authentication required\n'));
  return await authenticateAdmin();
}

/**
 * Check if currently authenticated as admin
 */
export function isAuthenticated(): boolean {
  return authState.token !== null && authState.role === 'admin';
}

/**
 * Get current auth token
 */
export function getAuthToken(): string | null {
  return authState.token;
}

/**
 * Clear auth state
 */
export function clearAuth(): void {
  authState = {
    token: null,
    username: null,
    role: null
  };
}
