/**
 * ServerStatsCard Test Suite
 *
 * Tests for the ServerStatsCard component that displays
 * server statistics with an icon.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Server, Wifi, AlertCircle } from 'lucide-react'
import { ServerStatsCard } from '../ServerStatsCard'

describe('ServerStatsCard', () => {
  const defaultProps = {
    title: 'Total Servers',
    value: 5,
    icon: Server,
    iconColor: 'text-blue-500',
    bgColor: 'blue.50'
  }

  describe('Rendering', () => {
    it('should render title', () => {
      render(<ServerStatsCard {...defaultProps} />)

      expect(screen.getByText('Total Servers')).toBeInTheDocument()
    })

    it('should render numeric value', () => {
      render(<ServerStatsCard {...defaultProps} value={10} />)

      expect(screen.getByText('10')).toBeInTheDocument()
    })

    it('should render string value', () => {
      render(<ServerStatsCard {...defaultProps} value="100%" />)

      expect(screen.getByText('100%')).toBeInTheDocument()
    })

    it('should render zero value', () => {
      render(<ServerStatsCard {...defaultProps} value={0} />)

      expect(screen.getByText('0')).toBeInTheDocument()
    })
  })

  describe('Different Stats', () => {
    it('should render connected servers stat', () => {
      render(
        <ServerStatsCard
          title="Connected"
          value={3}
          icon={Wifi}
          iconColor="text-green-500"
          bgColor="green.50"
        />
      )

      expect(screen.getByText('Connected')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
    })

    it('should render error count stat', () => {
      render(
        <ServerStatsCard
          title="Errors"
          value={2}
          icon={AlertCircle}
          iconColor="text-red-500"
          bgColor="red.50"
        />
      )

      expect(screen.getByText('Errors')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
    })
  })
})
