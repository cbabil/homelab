/**
 * Test setup for dashboard tests
 *
 * Mocks MUI components for testing.
 */

import React from 'react'
import { vi } from 'vitest'

interface CardProps {
  children: React.ReactNode
  className?: string
  elevation?: number
}

interface ChipProps {
  label: React.ReactNode
  color?: string
  size?: string
}

interface SkeletonProps {
  width?: string | number
  height?: string | number
  className?: string
  variant?: string
}

// Mock MUI components
vi.mock('@mui/material', async () => {
  const actual = (await vi.importActual('@mui/material')) as Record<string, unknown>
  return {
    ...actual,
    Card: ({ children, className, elevation }: CardProps) => (
      <div className={`mock-card ${className || ''}`} data-elevation={elevation}>
        {children}
      </div>
    ),
    Chip: ({ label, color, size }: ChipProps) => (
      <span className="mock-chip" data-color={color} data-size={size}>
        {label}
      </span>
    ),
    Skeleton: ({ width, height, className, variant }: SkeletonProps) => (
      <div
        className={`mock-skeleton ${className || ''}`}
        style={{ width, height }}
        data-testid="skeleton"
        data-variant={variant}
      />
    )
  }
})
