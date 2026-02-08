/**
 * CLI Authentication module
 *
 * Handles admin authentication for CLI commands.
 */

import { getMCPClient } from './mcp-client.js';

interface LoginResponse {
  token: string;
  refresh_token?: string;
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
  refreshToken: string | null;
  username: string | null;
  role: string | null;
}

interface AuthResult {
  success: boolean;
  error?: string;
}

// Closure-based auth state — no direct mutation from outside
const createAuthStore = () => {
  let state: AuthState = {
    token: null,
    refreshToken: null,
    username: null,
    role: null,
  };
  let generation = 0;

  return {
    isAuthenticated: (): boolean => state.token !== null && state.role === 'admin',
    getToken: (): string | null => state.token,
    getRefreshToken: (): string | null => state.refreshToken,
    getUsername: (): string | null => state.username,
    getRole: (): string | null => state.role,
    getGeneration: (): number => generation,
    set: (newState: AuthState): void => {
      state = { ...newState };
      generation++;
    },
    clear: (): void => {
      state = { token: null, refreshToken: null, username: null, role: null };
      generation++;
    },
  };
};

const authStore = createAuthStore();

/**
 * Basic sanity check that a token looks valid (non-empty string, min length).
 */
function isValidToken(token: unknown): token is string {
  return typeof token === 'string' && token.length >= 10;
}

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
 * Authenticate with provided credentials.
 * Returns an AuthResult indicating success or failure with error message.
 */
export async function authenticateAdmin(
  username: string,
  password: string
): Promise<AuthResult> {
  const client = getMCPClient();
  const response = await client.callTool<LoginResponse>('login', {
    username,
    password,
  });

  if (response.success && response.data) {
    const { token, refresh_token, user } = response.data;

    if (!isValidToken(token)) {
      return { success: false, error: 'Invalid token received from server' };
    }

    if (user.role !== 'admin') {
      return { success: false, error: 'Only admin users can run CLI commands' };
    }

    authStore.set({
      token,
      refreshToken: refresh_token ?? null,
      username: user.username,
      role: user.role,
    });

    return { success: true };
  }

  return { success: false, error: 'Invalid credentials' };
}

/**
 * Get the current auth token (for sending in API requests)
 */
export function getAuthToken(): string | null {
  return authStore.getToken();
}

/**
 * Get the current refresh token
 */
export function getRefreshToken(): string | null {
  return authStore.getRefreshToken();
}

/**
 * Get the current username
 */
export function getUsername(): string | null {
  return authStore.getUsername();
}

/**
 * Get the current role
 */
export function getRole(): string | null {
  return authStore.getRole();
}

// Mutex for deduplicating concurrent refresh attempts
let refreshInProgress: Promise<boolean> | null = null;

/**
 * Clear auth state (used for testing and logout)
 */
export function clearAuth(): void {
  authStore.clear();
  refreshInProgress = null;
}

/**
 * Revoke access and refresh tokens on the server (best-effort), then clear client state.
 * Captures tokens before clearing to avoid race conditions.
 */
export async function revokeToken(): Promise<void> {
  const token = authStore.getToken();
  const refreshToken = authStore.getRefreshToken();
  authStore.clear();

  const client = getMCPClient();
  const revocations: Promise<unknown>[] = [];

  if (token) {
    revocations.push(client.callToolRaw('revoke_token', { token }));
  }
  if (refreshToken) {
    revocations.push(client.callToolRaw('revoke_token', { token: refreshToken }));
  }

  if (revocations.length > 0) {
    await Promise.allSettled(revocations);
  }
}

async function doRefresh(): Promise<boolean> {
  const genBefore = authStore.getGeneration();
  try {
    const refreshToken = authStore.getRefreshToken();
    if (!refreshToken) {
      authStore.clear();
      return false;
    }

    const client = getMCPClient();
    const response = await client.callToolRaw<LoginResponse>('refresh_token', {
      refresh_token: refreshToken,
    });

    if (response.success && response.data) {
      // Abort if auth state changed while refresh was in-flight (e.g. logout/timeout)
      if (authStore.getGeneration() !== genBefore) {
        return false;
      }

      const { token, refresh_token, user } = response.data;
      if (!isValidToken(token)) {
        authStore.clear();
        return false;
      }

      authStore.set({
        token,
        refreshToken: refresh_token ?? null,
        username: user.username,
        role: user.role,
      });
      return true;
    }

    authStore.clear();
    return false;
  } catch {
    authStore.clear();
    return false;
  } finally {
    refreshInProgress = null;
  }
}

/**
 * Refresh the auth token using the stored refresh token.
 * Deduplicates concurrent calls via a shared promise.
 */
export async function refreshAuthToken(): Promise<boolean> {
  if (!authStore.getToken()) {
    return false;
  }
  if (refreshInProgress) {
    return refreshInProgress;
  }
  refreshInProgress = doRefresh();
  return refreshInProgress;
}
