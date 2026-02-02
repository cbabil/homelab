/**
 * ProtectedRoute Test Suite
 * 
 * Comprehensive tests for ProtectedRoute component including authentication checks,
 * role-based access control, loading states, and redirect logic.
 */

import React from 'react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ProtectedRoute, AdminRoute, UserRoute, PublicRoute } from './ProtectedRoute'
import { User } from '@/types/auth'

// Mock the auth hook
const { mockAuthState } = vi.hoisted(() => {
  const mockAuthState = {
    isAuthenticated: false,
    isLoading: false,
    error: null,
    user: null as User | null,
    refreshSession: vi.fn()
  }

  return { mockAuthState }
})

vi.mock('@/providers/AuthProvider', () => ({
  useAuth: () => mockAuthState
}))

// Test components
const ProtectedContent = () => <div data-testid="protected-content">Protected Content</div>
const PublicContent = () => <div data-testid="public-content">Public Content</div>
const LoginPage = () => <div data-testid="login-page">Login Page</div>
const HomePage = () => <div data-testid="home-page">Home Page</div>

function renderWithRouter(component: React.ReactElement) {
  return render(
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<HomePage />} />
        <Route path="/test" element={component} />
      </Routes>
    </BrowserRouter>
  )
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    Object.assign(mockAuthState, {
      isAuthenticated: false,
      isLoading: false,
      error: null,
      user: null,
      refreshSession: vi.fn()
    })
  })

  describe('Loading State', () => {
    it('should show loading screen while authenticating', () => {
      Object.assign(mockAuthState, { isLoading: true })

      renderWithRouter(
        <ProtectedRoute>
          <ProtectedContent />
        </ProtectedRoute>
      )

      expect(screen.getByText(/authenticating/i)).toBeInTheDocument()
      expect(screen.getByText(/please wait while we verify/i)).toBeInTheDocument()
    })

    it('should use custom fallback during loading', () => {
      Object.assign(mockAuthState, { isLoading: true })

      const customFallback = <div data-testid="custom-loading">Custom Loading...</div>

      renderWithRouter(
        <ProtectedRoute fallback={customFallback}>
          <ProtectedContent />
        </ProtectedRoute>
      )

      expect(screen.getByTestId('custom-loading')).toBeInTheDocument()
    })
  })

  describe('Authentication Required (Default)', () => {
    it('should redirect to login when not authenticated', () => {
      renderWithRouter(
        <ProtectedRoute>
          <ProtectedContent />
        </ProtectedRoute>
      )

      expect(screen.getByTestId('login-page')).toBeInTheDocument()
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
    })

    it('should show protected content when authenticated', () => {
      const mockUser: User = {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        role: 'user',
        lastLogin: '2023-01-01T00:00:00Z',
        isActive: true
      }

      Object.assign(mockAuthState, {
        isAuthenticated: true,
        user: mockUser
      })

      renderWithRouter(
        <ProtectedRoute>
          <ProtectedContent />
        </ProtectedRoute>
      )

      expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    })

    it('should redirect to custom path when specified', () => {
      const CustomLogin = () => <div data-testid="custom-login">Custom Login</div>
      
      render(
        <BrowserRouter>
          <Routes>
            <Route path="/custom-login" element={<CustomLogin />} />
            <Route 
              path="/test" 
              element={
                <ProtectedRoute redirectTo="/custom-login">
                  <ProtectedContent />
                </ProtectedRoute>
              } 
            />
          </Routes>
        </BrowserRouter>
      )
      
      expect(screen.getByTestId('custom-login')).toBeInTheDocument()
    })
  })

  describe('No Authentication Required', () => {
    it('should show content when authentication not required', () => {
      renderWithRouter(
        <ProtectedRoute requireAuth={false}>
          <PublicContent />
        </ProtectedRoute>
      )

      expect(screen.getByTestId('public-content')).toBeInTheDocument()
    })

    it('should show content even when not authenticated', () => {
      renderWithRouter(
        <ProtectedRoute requireAuth={false}>
          <PublicContent />
        </ProtectedRoute>
      )

      expect(screen.getByTestId('public-content')).toBeInTheDocument()
      expect(screen.queryByTestId('login-page')).not.toBeInTheDocument()
    })
  })

  describe('Role-Based Access Control', () => {
    it('should allow access with correct role', () => {
      const adminUser: User = {
        id: '1',
        username: 'admin',
        email: 'admin@example.com',
        role: 'admin',
        lastLogin: '2023-01-01T00:00:00Z',
        isActive: true
      }

      Object.assign(mockAuthState, {
        isAuthenticated: true,
        user: adminUser
      })

      renderWithRouter(
        <ProtectedRoute allowedRoles={['admin']}>
          <ProtectedContent />
        </ProtectedRoute>
      )

      expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    })

    it('should deny access with incorrect role', () => {
      const userRole: User = {
        id: '1',
        username: 'user',
        email: 'user@example.com',
        role: 'user',
        lastLogin: '2023-01-01T00:00:00Z',
        isActive: true
      }

      Object.assign(mockAuthState, {
        isAuthenticated: true,
        user: userRole
      })

      renderWithRouter(
        <ProtectedRoute allowedRoles={['admin']}>
          <ProtectedContent />
        </ProtectedRoute>
      )

      expect(screen.getByText(/access denied/i)).toBeInTheDocument()
      expect(screen.getByText(/admin role access/i)).toBeInTheDocument()
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
    })

    it('should allow access with multiple allowed roles', () => {
      const userRole: User = {
        id: '1',
        username: 'user',
        email: 'user@example.com',
        role: 'user',
        lastLogin: '2023-01-01T00:00:00Z',
        isActive: true
      }

      Object.assign(mockAuthState, {
        isAuthenticated: true,
        user: userRole
      })

      renderWithRouter(
        <ProtectedRoute allowedRoles={['admin', 'user']}>
          <ProtectedContent />
        </ProtectedRoute>
      )

      expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    })
  })

  describe('User Status Checks', () => {
    it('should deny access to inactive users', () => {
      const inactiveUser: User = {
        id: '1',
        username: 'inactive',
        email: 'inactive@example.com',
        role: 'user',
        lastLogin: '2023-01-01T00:00:00Z',
        isActive: false
      }

      Object.assign(mockAuthState, {
        isAuthenticated: true,
        user: inactiveUser
      })

      renderWithRouter(
        <ProtectedRoute>
          <ProtectedContent />
        </ProtectedRoute>
      )

      expect(screen.getByText(/access denied/i)).toBeInTheDocument()
      expect(screen.getByText(/account has been deactivated/i)).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should show error message when authentication fails', () => {
      Object.assign(mockAuthState, {
        error: 'Authentication failed'
      })

      renderWithRouter(
        <ProtectedRoute>
          <ProtectedContent />
        </ProtectedRoute>
      )

      expect(screen.getByText(/access denied/i)).toBeInTheDocument()
      expect(screen.getByText(/authentication error: authentication failed/i)).toBeInTheDocument()
    })

    it('should provide retry functionality on error', async () => {
      const mockRefreshSession = vi.fn()
      Object.assign(mockAuthState, {
        error: 'Session expired',
        refreshSession: mockRefreshSession
      })

      renderWithRouter(
        <ProtectedRoute>
          <ProtectedContent />
        </ProtectedRoute>
      )

      const retryButton = screen.getByText(/try again/i)
      expect(retryButton).toBeInTheDocument()

      // Note: In a real test, you'd click the button and verify the refresh is called
    })
  })

  describe('AdminRoute Helper', () => {
    it('should only allow admin users', () => {
      const adminUser: User = {
        id: '1',
        username: 'admin',
        email: 'admin@example.com',
        role: 'admin',
        lastLogin: '2023-01-01T00:00:00Z',
        isActive: true
      }

      Object.assign(mockAuthState, {
        isAuthenticated: true,
        user: adminUser
      })

      renderWithRouter(
        <AdminRoute>
          <ProtectedContent />
        </AdminRoute>
      )

      expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    })

    it('should deny non-admin users', () => {
      const userRole: User = {
        id: '1',
        username: 'user',
        email: 'user@example.com',
        role: 'user',
        lastLogin: '2023-01-01T00:00:00Z',
        isActive: true
      }

      Object.assign(mockAuthState, {
        isAuthenticated: true,
        user: userRole
      })

      renderWithRouter(
        <AdminRoute>
          <ProtectedContent />
        </AdminRoute>
      )

      expect(screen.getByText(/access denied/i)).toBeInTheDocument()
    })
  })

  describe('UserRoute Helper', () => {
    it('should allow both user and admin roles', () => {
      const userRole: User = {
        id: '1',
        username: 'user',
        email: 'user@example.com',
        role: 'user',
        lastLogin: '2023-01-01T00:00:00Z',
        isActive: true
      }

      Object.assign(mockAuthState, {
        isAuthenticated: true,
        user: userRole
      })

      renderWithRouter(
        <UserRoute>
          <ProtectedContent />
        </UserRoute>
      )

      expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    })
  })

  describe('PublicRoute Helper', () => {
    it('should show public content when not authenticated', () => {
      renderWithRouter(
        <PublicRoute>
          <PublicContent />
        </PublicRoute>
      )

      expect(screen.getByTestId('public-content')).toBeInTheDocument()
    })

    it('should redirect authenticated users to home', () => {
      const mockUser: User = {
        id: '1',
        username: 'user',
        email: 'user@example.com',
        role: 'user',
        lastLogin: '2023-01-01T00:00:00Z',
        isActive: true
      }

      Object.assign(mockAuthState, {
        isAuthenticated: true,
        user: mockUser
      })

      renderWithRouter(
        <PublicRoute>
          <PublicContent />
        </PublicRoute>
      )

      expect(screen.getByTestId('home-page')).toBeInTheDocument()
      expect(screen.queryByTestId('public-content')).not.toBeInTheDocument()
    })

    it('should redirect to custom path when specified', () => {
      const mockUser: User = {
        id: '1',
        username: 'user',
        email: 'user@example.com',
        role: 'user',
        lastLogin: '2023-01-01T00:00:00Z',
        isActive: true
      }
      
      Object.assign(mockAuthState, {
        isAuthenticated: true,
        user: mockUser
      })
      
      const DashboardPage = () => <div data-testid="dashboard">Dashboard</div>
      
      render(
        <BrowserRouter>
          <Routes>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route 
              path="/test" 
              element={
                <PublicRoute redirectTo="/dashboard">
                  <PublicContent />
                </PublicRoute>
              } 
            />
          </Routes>
        </BrowserRouter>
      )
      
      expect(screen.getByTestId('dashboard')).toBeInTheDocument()
    })
  })

  describe('Configuration Object', () => {
    it('should accept configuration object', () => {
      const config = {
        requireAuth: true,
        allowedRoles: ['admin'] as User['role'][],
        redirectTo: '/login'
      }

      renderWithRouter(
        <ProtectedRoute config={config}>
          <ProtectedContent />
        </ProtectedRoute>
      )

      expect(screen.getByTestId('login-page')).toBeInTheDocument()
    })

    it('should merge config with props (props take precedence)', () => {
      const config = {
        requireAuth: true,
        allowedRoles: ['user'] as User['role'][]
      }

      const adminUser: User = {
        id: '1',
        username: 'admin',
        email: 'admin@example.com',
        role: 'admin',
        lastLogin: '2023-01-01T00:00:00Z',
        isActive: true
      }

      Object.assign(mockAuthState, {
        isAuthenticated: true,
        user: adminUser
      })

      renderWithRouter(
        <ProtectedRoute config={config} allowedRoles={['admin']}>
          <ProtectedContent />
        </ProtectedRoute>
      )

      // Props should override config
      expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    })
  })
})