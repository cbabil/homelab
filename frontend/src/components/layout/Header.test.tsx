/**
 * Unit tests for Header Component
 *
 * Tests header rendering with user menu and navigation.
 * Covers authenticated user state with proper context.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { Header } from './Header'
import { ToastProvider } from '@/components/ui/Toast'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(() => null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock data services
vi.mock('@/hooks/useDataServices', () => ({
  useDataServices: () => ({
    factory: {
      clearDataCaches: vi.fn(),
      clearServiceCache: vi.fn()
    }
  })
}))

// Mock cache utils
vi.mock('@/utils/cacheUtils', () => ({
  clearTomoCaches: vi.fn()
}))

// Mock ThemeSwitcher to avoid localStorage issues
vi.mock('@/components/ui/ThemeSwitcher', () => ({
  ThemeSwitcher: () => <div data-testid="theme-switcher" />
}))

// Mock NotificationDropdown
vi.mock('@/components/ui/NotificationDropdown', () => ({
  NotificationDropdown: () => <div data-testid="notification-dropdown" />
}))

const mockUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  role: 'admin',
  isActive: true,
  lastLogin: new Date().toISOString()
}

const mockAuthContext = {
  user: mockUser,
  isAuthenticated: true,
  login: vi.fn(),
  logout: vi.fn(),
  register: vi.fn(),
  loading: false
}

vi.mock('@/providers/AuthProvider', async () => {
  const actual = await vi.importActual<typeof import('@/providers/AuthProvider')>('@/providers/AuthProvider')
  return {
    ...actual,
    useAuth: () => mockAuthContext
  }
})

function renderHeader() {
  return render(
    <BrowserRouter>
      <ToastProvider>
        <Header />
      </ToastProvider>
    </BrowserRouter>
  )
}

describe('Header Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('should render title and branding', () => {
    renderHeader()

    // Uses translations now
    expect(screen.getByText('Tomo')).toBeInTheDocument()
    expect(screen.getByText('Professional Edition')).toBeInTheDocument()
    expect(screen.getByAltText('Tomo Logo')).toBeInTheDocument()
  })

  it('should render user menu when user is authenticated', () => {
    renderHeader()

    expect(screen.getByText('testuser')).toBeInTheDocument()
    expect(screen.getByText('admin')).toBeInTheDocument()
  })

  it('should have proper header structure with MUI components', () => {
    renderHeader()

    const header = screen.getByRole('banner')
    expect(header).toBeInTheDocument()
  })

  it('should render theme switcher and notification dropdown', () => {
    renderHeader()

    expect(screen.getByTestId('theme-switcher')).toBeInTheDocument()
    expect(screen.getByTestId('notification-dropdown')).toBeInTheDocument()
  })

  it('should render user role in header', () => {
    renderHeader()

    // User role is visible in the header
    expect(screen.getByText('admin')).toBeInTheDocument()
  })
})
