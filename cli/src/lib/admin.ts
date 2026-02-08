/**
 * Admin management module
 *
 * Handles admin user creation and password management
 * using the MCP server for all database operations.
 */

import { getMCPClient } from './mcp-client.js';

interface AdminResult {
  success: boolean;
  error?: string;
}

interface AdminCreateData {
  username: string;
}

/**
 * Create a new admin user via MCP
 */
export async function createAdmin(
  username: string,
  password: string
): Promise<AdminResult> {
  const client = getMCPClient();
  const response = await client.callTool<AdminCreateData>('create_initial_admin', {
    username,
    password
  });

  if (response.success) {
    return { success: true };
  }

  return {
    success: false,
    error: response.error || response.message || 'Failed to create admin'
  };
}

/**
 * Reset a user's password via MCP
 */
export async function resetPassword(
  username: string,
  newPassword: string
): Promise<AdminResult> {
  const client = getMCPClient();
  const response = await client.callTool('reset_user_password', {
    username,
    password: newPassword
  });

  if (response.success) {
    return { success: true };
  }

  return {
    success: false,
    error: response.error || response.message || 'Failed to reset password'
  };
}
