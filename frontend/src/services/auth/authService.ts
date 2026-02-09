/**
 * Authentication Service
 *
 * Core authentication operations including login, token refresh,
 * and validation. Now integrated with JWT service for real token management.
 */

import type {
  LoginCredentials,
  User,
  LoginResponse,
  RegistrationCredentials,
  RegistrationResponse,
} from '@/types/auth';
import type { JWTGenerationOptions } from '@/types/jwt';
import { jwtService } from './jwtService';
import { TomoMCPClient } from '@/services/mcpClient';
import { cryptoRandomString } from '@/utils/jwtUtils';
import { securityLogger } from '@/services/systemLogger';

const MCP_CONNECTION_ERROR_PATTERNS = [
  'failed to connect to mcp server',
  'failed to fetch',
  'networkerror',
  'connection refused',
  'mcp_connection_error',
];

class AuthService {
  private isInitialized = false;
  private mcpClient!: TomoMCPClient;
  private offlineMode = false;

  /**
   * Initialize authentication service
   */
  async initialize(): Promise<void> {
    if (!this.isInitialized) {
      await jwtService.initialize();
      const serverUrl = import.meta.env.VITE_MCP_SERVER_URL || '/mcp';
      this.mcpClient = new TomoMCPClient(serverUrl);

      try {
        await this.mcpClient.connect();
        this.offlineMode = false;
      } catch (_error) {
        this.offlineMode = true;
        securityLogger.warn('MCP connection unavailable, enabling offline mode');
      }

      this.isInitialized = true;
    }
  }

  /**
   * Authenticate user with credentials
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    await this.ensureInitialized();

    // Try to reconnect if we're in offline mode
    if (this.offlineMode) {
      securityLogger.info('Currently in offline mode, attempting reconnection');
      await this.tryReconnect();
    }

    // Backend authentication is required - no offline fallback for auth
    if (this.offlineMode) {
      securityLogger.error('Cannot authenticate: backend unavailable');
      throw new Error('Authentication service unavailable. Please try again later.');
    }

    let user: User | null = null;

    try {
      securityLogger.info('Authenticating with backend');
      user = await this.authenticateWithBackend(credentials);
      securityLogger.info('Backend authentication successful');
    } catch (error) {
      securityLogger.warn('Backend authentication failed', { error: String(error) });
      const connectionFailure = this.isConnectionError(error);

      if (connectionFailure) {
        this.offlineMode = true;
        throw new Error('Authentication service unavailable. Please try again later.');
      }
      throw error;
    }

    if (!user) {
      throw new Error('Invalid username or password');
    }

    const sessionId = this.generateSessionId();
    const userAgent = navigator.userAgent;
    const ipAddress = await this.getClientIP();

    const jwtOptions: JWTGenerationOptions = {
      userId: user.id,
      username: user.username,
      email: user.email || `${user.username}@tomo.local`,
      role: user.role,
      sessionId,
      userAgent,
      ipAddress,
      tokenType: 'access',
      scope: user.role === 'admin' ? ['read', 'write', 'admin'] : ['read'],
      preferences: user.preferences,
    };

    const { accessToken, refreshToken } = await this.issueTokens(jwtOptions);

    return {
      user,
      token: accessToken,
      refreshToken,
      expiresIn: 3600,
    };
  }

  /**
   * Register new user with credentials
   */
  async register(credentials: RegistrationCredentials): Promise<RegistrationResponse> {
    await this.ensureInitialized();

    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Validate registration data
    await this.validateRegistrationCredentials(credentials);

    // Create new user account
    const user = await this.createUserAccount(credentials);

    // Generate session ID for JWT claims
    const sessionId = this.generateSessionId();
    const userAgent = navigator.userAgent;
    const ipAddress = await this.getClientIP();

    // Create JWT generation options
    const jwtOptions: JWTGenerationOptions = {
      userId: user.id,
      username: user.username,
      email: user.email || `${user.username}@tomo.local`,
      role: user.role,
      sessionId,
      userAgent,
      ipAddress,
      tokenType: 'access',
      scope: user.role === 'admin' ? ['read', 'write', 'admin'] : ['read'],
      preferences: user.preferences,
    };

    const { accessToken, refreshToken } = await this.issueTokens(jwtOptions);

    return {
      user,
      token: accessToken,
      refreshToken,
      expiresIn: 3600, // 1 hour
      isEmailVerified: false, // In real implementation, would require email verification
      tokenType: 'JWT',
    };
  }

  /**
   * Refresh authentication token using JWT refresh flow
   */
  async refreshToken(refreshToken: string): Promise<LoginResponse> {
    await this.ensureInitialized();

    // Use JWT service to refresh tokens
    const tokenPair = await jwtService.refreshToken(refreshToken);

    // Decode the new access token to extract user data
    const decodedToken = jwtService.decodeToken(tokenPair.accessToken);
    if (!decodedToken?.payload) {
      throw new Error('Session expired. Please log in again.');
    }

    const payload = decodedToken.payload;
    const user: User = {
      id: payload.id,
      username: payload.username,
      email: payload.email,
      role: payload.role,
      lastLogin: new Date().toISOString(),
      isActive: true,
      preferences: payload.preferences,
    };

    return {
      user,
      token: tokenPair.accessToken,
      refreshToken: tokenPair.refreshToken,
      expiresIn: tokenPair.expiresIn,
    };
  }

  /**
   * Validate authentication token using JWT verification
   */
  async validateToken(token: string): Promise<boolean> {
    await this.ensureInitialized();

    try {
      const validation = await jwtService.validateToken(token);
      return validation.isValid;
    } catch (error) {
      securityLogger.error('Token validation error', { error: String(error) });
      return false;
    }
  }

  /**
   * Logout and revoke tokens
   */
  async logout(token?: string, fallbackUsername?: string): Promise<void> {
    await this.ensureInitialized();

    try {
      // Extract session_id from token for backend logout logging
      let sessionId = 'unknown';
      if (token) {
        try {
          const decodedToken = jwtService.decodeToken(token);
          sessionId = decodedToken?.payload?.sessionId || 'unknown';
        } catch (_e) {
          securityLogger.warn('Could not decode token for logout logging');
        }

        // Revoke the access token
        await jwtService.revokeToken(token, 'logout');
      }

      // Call backend logout with session context and user info for logging
      if (!this.offlineMode) {
        try {
          // Extract username from token or use fallback
          let username = 'unknown';
          if (token) {
            try {
              const decodedToken = jwtService.decodeToken(token);
              username = decodedToken?.payload?.username || 'unknown';
            } catch (e) {
              securityLogger.warn('Could not extract username from token for logout', {
                error: String(e),
              });
              if (fallbackUsername) {
                username = fallbackUsername;
              }
            }
          } else if (fallbackUsername) {
            username = fallbackUsername;
          }

          const logoutResult = await this.mcpClient.callTool('logout', {
            session_id: sessionId,
            username: username !== 'unknown' ? username : undefined,
          });

          if (!logoutResult.success && logoutResult.error) {
            const wrappedError = new Error(String(logoutResult.error));
            if (this.isConnectionError(wrappedError)) {
              this.offlineMode = true;
              securityLogger.warn('MCP logout skipped due to connection issue');
            } else {
              securityLogger.error('Backend logout logging failed', {
                error: String(logoutResult.error),
              });
            }
          }
        } catch (error) {
          if (this.isConnectionError(error)) {
            this.offlineMode = true;
            securityLogger.warn('MCP logout skipped due to connection issue');
          } else {
            securityLogger.error('Backend logout logging failed', { error: String(error) });
          }
          // Continue with logout even if backend logging fails
        }
      }

      // Simulate logout delay
      await new Promise((resolve) => setTimeout(resolve, 200));
    } catch (error) {
      securityLogger.error('Logout error', { error: String(error) });
      // Don't throw - allow logout to proceed even if revocation fails
    }
  }

  /**
   * Attempt to re-establish MCP connection when offline
   */
  private async tryReconnect(): Promise<void> {
    try {
      await this.mcpClient.connect();
      this.offlineMode = false;
    } catch (_error) {
      securityLogger.warn('MCP reconnection attempt failed');
      this.offlineMode = true;
    }
  }

  private isConnectionError(error: unknown): boolean {
    if (error instanceof Error) {
      const message = error.message.toLowerCase();
      return MCP_CONNECTION_ERROR_PATTERNS.some((pattern) => message.includes(pattern));
    }
    return false;
  }

  private async issueTokens(
    options: JWTGenerationOptions
  ): Promise<{ accessToken: string; refreshToken: string }> {
    try {
      const accessToken = await jwtService.generateToken({ ...options, tokenType: 'access' });
      const refreshToken = await jwtService.generateToken({ ...options, tokenType: 'refresh' });
      return { accessToken, refreshToken };
    } catch (_error) {
      securityLogger.warn('JWT generation failed, using fallback tokens');
      return {
        accessToken: this.createFallbackToken(options, 'access'),
        refreshToken: this.createFallbackToken(options, 'refresh'),
      };
    }
  }

  private createFallbackToken(
    options: JWTGenerationOptions,
    tokenType: 'access' | 'refresh'
  ): string {
    const payload = {
      userId: options.userId,
      username: options.username,
      role: options.role,
      tokenType,
      issuedAt: Date.now(),
      sessionId: options.sessionId,
    };

    try {
      const serialized = JSON.stringify(payload);
      const encoded = this.encodeBase64(serialized);
      if (encoded) {
        return `offline-${tokenType}-${encoded}`;
      }
    } catch (_error) {
      securityLogger.warn('Unable to encode fallback token payload');
    }

    return `offline-${tokenType}-${payload.userId}-${payload.issuedAt}`;
  }

  private encodeBase64(value: string): string | null {
    try {
      if (typeof globalThis !== 'undefined' && typeof globalThis.btoa === 'function') {
        return globalThis.btoa(value);
      }
    } catch (_error) {
      securityLogger.warn('Base64 encode failed');
    }
    return null;
  }

  /**
   * Authenticate user with backend MCP service
   */
  private async authenticateWithBackend(credentials: LoginCredentials): Promise<User> {
    try {
      await this.ensureInitialized();

      if (this.offlineMode) {
        throw new Error('MCP_CONNECTION_ERROR: offline mode enabled');
      }

      const response = await this.mcpClient.callTool('login', {
        credentials: {
          username: credentials.username,
          password: credentials.password,
        },
      });

      if (!response.success) {
        const errorData = response.data as { message?: string } | undefined;
        const errorMessage = response.error || errorData?.message || 'Authentication failed';
        const wrappedError = new Error(errorMessage);
        if (this.isConnectionError(wrappedError)) {
          throw new Error(`MCP_CONNECTION_ERROR: ${errorMessage}`);
        }
        // Pass through the backend error message directly
        throw new Error(errorMessage);
      }

      // MCP client already extracts structuredContent into response.data
      // The login tool returns { success: true, data: { user: {...} } }
      interface BackendUser {
        id?: string;
        username: string;
        email?: string;
        role?: string;
        is_active?: boolean;
        created_at?: string;
        preferences?: Record<string, unknown>;
      }

      interface LoginToolResponse {
        data?: { user: BackendUser };
        user?: BackendUser;
      }

      const typedData = response.data as LoginToolResponse;
      const userData = typedData?.data?.user || typedData?.user;

      if (!userData) {
        // Pass through the backend error message directly
        const errorData = response.data as { message?: string } | undefined;
        const errorMessage = errorData?.message || response.error || 'Authentication failed';
        securityLogger.error('No user data in response');
        throw new Error(errorMessage);
      }

      const user: User = {
        id: userData.id || userData.username,
        username: userData.username,
        email: userData.email || `${userData.username}@tomo.local`,
        role: (userData.role as 'admin' | 'user') || 'user',
        lastLogin: new Date().toISOString(),
        isActive: userData.is_active !== false,
        createdAt: userData.created_at,
        preferences: userData.preferences || {},
      };

      securityLogger.info('User authenticated');
      return user;
    } catch (error) {
      if (this.isConnectionError(error)) {
        const connectionError = error instanceof Error ? error : new Error('MCP_CONNECTION_ERROR');
        throw connectionError;
      }

      securityLogger.error('Backend authentication error', { error: String(error) });
      // Re-throw the original error message
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Authentication failed');
    }
  }

  /**
   * Generate session ID for JWT claims
   */
  private generateSessionId(): string {
    return 'sess_' + cryptoRandomString(16);
  }

  /**
   * Get client IP (mock implementation)
   */
  private async getClientIP(): Promise<string> {
    // In production, this would be obtained from request headers
    return '127.0.0.1';
  }

  /**
   * Validate registration credentials (security measures)
   */
  private async validateRegistrationCredentials(
    credentials: RegistrationCredentials
  ): Promise<void> {
    // Username uniqueness check (generic error for security)
    if (await this.usernameExists(credentials.username)) {
      throw new Error('Invalid username or password');
    }

    // Email uniqueness check (generic error for security)
    if (await this.emailExists(credentials.email)) {
      throw new Error('Invalid username or password');
    }

    // Password confirmation validation
    if (credentials.password !== credentials.confirmPassword) {
      throw new Error('Invalid username or password');
    }

    // Terms acceptance validation
    if (!credentials.acceptTerms) {
      throw new Error('Invalid username or password');
    }
  }

  /**
   * Create new user account (mock implementation)
   */
  private async createUserAccount(credentials: RegistrationCredentials): Promise<User> {
    // Generate unique user ID
    const userId = 'user_' + cryptoRandomString(10);

    return {
      id: userId,
      username: credentials.username,
      email: credentials.email,
      role: credentials.role || 'user', // Default to user role
      lastLogin: new Date().toISOString(),
      isActive: true,
      preferences: {
        theme: 'dark', // Default preferences for new users
        notifications: true,
      },
    };
  }

  /**
   * Check if username already exists (mock implementation)
   */
  private async usernameExists(username: string): Promise<boolean> {
    // Simulate API delay for consistent response timing
    await new Promise((resolve) => setTimeout(resolve, 200));

    // Mock check - in production, query database
    const existingUsernames = ['admin', 'user', 'test', 'demo'];
    return existingUsernames.includes(username.toLowerCase());
  }

  /**
   * Check if email already exists (mock implementation)
   */
  private async emailExists(email: string): Promise<boolean> {
    // Simulate API delay for consistent response timing
    await new Promise((resolve) => setTimeout(resolve, 200));

    // Mock check - in production, query database
    const existingEmails = ['admin@tomo.local', 'user@tomo.local', 'test@example.com'];
    return existingEmails.includes(email.toLowerCase());
  }

  /**
   * Ensure service is initialized
   */
  private async ensureInitialized(): Promise<void> {
    if (!this.isInitialized) {
      await this.initialize();
    }
  }
}

export const authService = new AuthService();
export default authService;
