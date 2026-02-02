/**
 * Admin management module
 *
 * Handles admin user creation and password management
 * using the MCP server for all database operations.
 */

import { getMCPClient } from './mcp-client.js';

export interface User {
  id: string;
  username: string;
  email?: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminResult {
  success: boolean;
  error?: string;
}

interface UserData {
  id: string;
  username: string;
  email?: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface AdminCreateData {
  username: string;
}

/**
 * Get a user by username via MCP
 */
export async function getUser(username: string): Promise<User | null> {
  const client = getMCPClient();
  const response = await client.callTool<UserData>('get_user_by_username', { username });

  if (response.success && response.data) {
    return {
      id: response.data.id,
      username: response.data.username,
      email: response.data.email,
      role: response.data.role,
      is_active: response.data.is_active,
      created_at: response.data.created_at,
      updated_at: response.data.updated_at
    };
  }

  return null;
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
