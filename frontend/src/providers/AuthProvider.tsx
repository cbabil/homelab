/**
 * Authentication Provider
 *
 * Secure authentication provider with JWT token support, cookie-based session management,
 * activity tracking, and settings integration.
 */

import React, { createContext, useContext } from 'react';
import type { AuthContextType } from '@/types/auth';
import type { JWTPayload } from '@/types/jwt';
import { useAuthState } from '@/hooks/useAuthState';
import { useAuthActions } from '@/hooks/useAuthActions';
import { authService } from '@/services/auth/authService';

// Create authentication context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  // Use extracted hooks for state and actions
  const { authState, updateAuthState, clearAuthState } = useAuthState();
  const { login, register, logout, refreshSession } = useAuthActions({
    authState,
    updateAuthState,
    clearAuthState,
  });

  // JWT-specific methods
  const validateToken = async (token?: string): Promise<boolean> => {
    if (!token && !authState.isAuthenticated) {
      return false;
    }
    return await authService.validateToken(token || '');
  };

  const getTokenMetadata = (): Partial<JWTPayload> | null => {
    return authState.tokenMetadata || null;
  };

  const isTokenExpired = (): boolean => {
    if (!authState.tokenExpiry) return false;
    return new Date(authState.tokenExpiry) <= new Date();
  };

  // Session management methods (placeholders for compatibility)
  const recordActivity = (): void => {
    // Placeholder: will be implemented when session hooks are updated
  };

  const dismissWarning = (): void => {
    // Placeholder: will be implemented when session hooks are updated
  };

  const extendSession = async (): Promise<void> => {
    // Placeholder: will be implemented when session hooks are updated
  };

  // Create context value with all auth functionality
  const contextValue: AuthContextType = {
    authState,
    login,
    register,
    logout,
    refreshSession,

    // Session management
    recordActivity,
    dismissWarning,
    extendSession,

    // JWT-specific methods
    validateToken,
    getTokenMetadata,
    isTokenExpired,

    // Utilities
    isAuthenticated: authState.isAuthenticated,
    isLoading: authState.isLoading,
    user: authState.user,
    error: authState.error,
    activity: authState.activity,
    warning: authState.warning,
    tokenType: authState.tokenType || null,
    tokenExpiry: authState.tokenExpiry || null,
  };

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
}

// Custom hook to use authentication context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}

// Export for testing purposes
export { AuthContext };
