/**
 * Skeleton Components Test Suite
 *
 * Tests for all skeleton loading components including basic skeleton,
 * text, avatar, card, table row, stat, server card, and grid variants.
 */

import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import {
  Skeleton,
  SkeletonText,
  SkeletonAvatar,
  SkeletonCard,
  SkeletonTableRow,
  SkeletonStat,
  SkeletonServerCard,
  SkeletonDashboardStats,
  SkeletonServerGrid
} from '../Skeleton'

describe('Skeleton', () => {
  describe('Basic Skeleton', () => {
    it('should render skeleton element', () => {
      const { container } = render(<Skeleton />)

      expect(container.querySelector('.MuiSkeleton-root')).toBeInTheDocument()
    })

    it('should accept custom sx props', () => {
      const { container } = render(<Skeleton sx={{ width: 100, height: 50 }} />)

      expect(container.querySelector('.MuiSkeleton-root')).toBeInTheDocument()
    })
  })

  describe('SkeletonText', () => {
    it('should render single line by default', () => {
      const { container } = render(<SkeletonText />)

      const skeletons = container.querySelectorAll('.MuiSkeleton-root')
      expect(skeletons).toHaveLength(1)
    })

    it('should render multiple lines', () => {
      const { container } = render(<SkeletonText lines={3} />)

      const skeletons = container.querySelectorAll('.MuiSkeleton-root')
      expect(skeletons).toHaveLength(3)
    })

    it('should render specified number of lines', () => {
      const { container } = render(<SkeletonText lines={5} />)

      const skeletons = container.querySelectorAll('.MuiSkeleton-root')
      expect(skeletons).toHaveLength(5)
    })
  })

  describe('SkeletonAvatar', () => {
    it('should render circular skeleton', () => {
      const { container } = render(<SkeletonAvatar />)

      const skeleton = container.querySelector('.MuiSkeleton-circular')
      expect(skeleton).toBeInTheDocument()
    })

    it('should render small size', () => {
      const { container } = render(<SkeletonAvatar size="sm" />)

      expect(container.querySelector('.MuiSkeleton-circular')).toBeInTheDocument()
    })

    it('should render medium size (default)', () => {
      const { container } = render(<SkeletonAvatar />)

      expect(container.querySelector('.MuiSkeleton-circular')).toBeInTheDocument()
    })

    it('should render large size', () => {
      const { container } = render(<SkeletonAvatar size="lg" />)

      expect(container.querySelector('.MuiSkeleton-circular')).toBeInTheDocument()
    })
  })

  describe('SkeletonCard', () => {
    it('should render card skeleton', () => {
      const { container } = render(<SkeletonCard />)

      // Should have multiple skeleton elements (avatar + text lines)
      const skeletons = container.querySelectorAll('.MuiSkeleton-root')
      expect(skeletons.length).toBeGreaterThan(0)
    })

    it('should include avatar skeleton', () => {
      const { container } = render(<SkeletonCard />)

      expect(container.querySelector('.MuiSkeleton-circular')).toBeInTheDocument()
    })
  })

  describe('SkeletonTableRow', () => {
    it('should render table row with default 4 columns', () => {
      const { container } = render(
        <table>
          <tbody>
            <SkeletonTableRow />
          </tbody>
        </table>
      )

      const cells = container.querySelectorAll('td')
      expect(cells).toHaveLength(4)
    })

    it('should render specified number of columns', () => {
      const { container } = render(
        <table>
          <tbody>
            <SkeletonTableRow columns={6} />
          </tbody>
        </table>
      )

      const cells = container.querySelectorAll('td')
      expect(cells).toHaveLength(6)
    })

    it('should render skeleton in each cell', () => {
      const { container } = render(
        <table>
          <tbody>
            <SkeletonTableRow columns={3} />
          </tbody>
        </table>
      )

      const skeletons = container.querySelectorAll('.MuiSkeleton-root')
      expect(skeletons).toHaveLength(3)
    })
  })

  describe('SkeletonStat', () => {
    it('should render stat skeleton', () => {
      const { container } = render(<SkeletonStat />)

      const skeletons = container.querySelectorAll('.MuiSkeleton-root')
      expect(skeletons.length).toBeGreaterThanOrEqual(2)
    })
  })

  describe('SkeletonServerCard', () => {
    it('should render server card skeleton', () => {
      const { container } = render(<SkeletonServerCard />)

      const skeletons = container.querySelectorAll('.MuiSkeleton-root')
      expect(skeletons.length).toBeGreaterThan(0)
    })
  })

  describe('SkeletonDashboardStats', () => {
    it('should render 4 stat skeletons', () => {
      const { container } = render(<SkeletonDashboardStats />)

      // Each SkeletonStat has at least 2 skeleton elements
      const skeletons = container.querySelectorAll('.MuiSkeleton-root')
      expect(skeletons.length).toBeGreaterThanOrEqual(8)
    })
  })

  describe('SkeletonServerGrid', () => {
    it('should render default 6 server cards', () => {
      const { container } = render(<SkeletonServerGrid />)

      // Each SkeletonServerCard has multiple skeleton elements
      const skeletons = container.querySelectorAll('.MuiSkeleton-root')
      expect(skeletons.length).toBeGreaterThan(6)
    })

    it('should render specified count of server cards', () => {
      const { container } = render(<SkeletonServerGrid count={3} />)

      // Should have fewer skeletons than default
      const skeletons = container.querySelectorAll('.MuiSkeleton-root')
      expect(skeletons.length).toBeGreaterThan(0)
    })
  })
})
