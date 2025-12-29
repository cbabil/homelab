/**
 * Test setup for dashboard tests
 *
 * Mocks ui-toolkit components that have React version compatibility issues.
 */

import { vi } from 'vitest'

// Mock ui-toolkit components
vi.mock('ui-toolkit', () => ({
  Card: ({ children, className, padding }: any) => (
    <div className={`mock-card ${className || ''}`} data-padding={padding}>
      {children}
    </div>
  ),
  Badge: ({ children, variant, size }: any) => (
    <span className={`mock-badge`} data-variant={variant} data-size={size}>
      {children}
    </span>
  ),
  Skeleton: ({ width, height, className }: any) => (
    <div
      className={`mock-skeleton ${className || ''}`}
      style={{ width, height }}
      data-testid="skeleton"
    />
  )
}))
