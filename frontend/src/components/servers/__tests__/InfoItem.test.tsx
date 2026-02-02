/**
 * InfoItem Test Suite
 *
 * Tests for the InfoItem component that displays
 * server information with icon and label/value pairs.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Monitor, Cpu, Container } from 'lucide-react'
import { InfoItem } from '../InfoItem'

describe('InfoItem', () => {
  describe('Rendering', () => {
    it('should render label', () => {
      render(<InfoItem icon={Monitor} label="OS" value="Ubuntu 22.04" />)

      expect(screen.getByText('OS')).toBeInTheDocument()
    })

    it('should render value', () => {
      render(<InfoItem icon={Monitor} label="OS" value="Ubuntu 22.04" />)

      expect(screen.getByText('Ubuntu 22.04')).toBeInTheDocument()
    })

    it('should apply className when provided', () => {
      const { container } = render(
        <InfoItem icon={Monitor} label="OS" value="Ubuntu" className="custom-class" />
      )

      expect(container.firstChild).toHaveClass('custom-class')
    })
  })

  describe('Not Available Messages', () => {
    it('should show Docker not installed for Docker label', () => {
      render(<InfoItem icon={Container} label="Docker Version" />)

      expect(screen.getByText('Docker not installed')).toBeInTheDocument()
    })

    it('should show OS information unavailable for OS label', () => {
      render(<InfoItem icon={Monitor} label="OS" />)

      expect(screen.getByText('OS information unavailable')).toBeInTheDocument()
    })

    it('should show Architecture unavailable for Architecture label', () => {
      render(<InfoItem icon={Cpu} label="Architecture" />)

      expect(screen.getByText('Architecture unavailable')).toBeInTheDocument()
    })

    it('should show Uptime unavailable for Uptime label', () => {
      render(<InfoItem icon={Monitor} label="Uptime" />)

      expect(screen.getByText('Uptime unavailable')).toBeInTheDocument()
    })

    it('should show Kernel info unavailable for Kernel label', () => {
      render(<InfoItem icon={Monitor} label="Kernel Version" />)

      expect(screen.getByText('Kernel info unavailable')).toBeInTheDocument()
    })

    it('should show Not available for unknown labels', () => {
      render(<InfoItem icon={Monitor} label="Custom" />)

      expect(screen.getByText('Not available')).toBeInTheDocument()
    })
  })

  describe('Value Styling', () => {
    it('should render with different font weight based on value presence', () => {
      render(<InfoItem icon={Monitor} label="OS" value="Ubuntu" />)

      // Value text should be present with fontWeight 500
      expect(screen.getByText('Ubuntu')).toBeInTheDocument()
    })

    it('should render italic style when no value', () => {
      render(<InfoItem icon={Monitor} label="Custom" />)

      // "Not available" should be present with italic styling
      expect(screen.getByText('Not available')).toBeInTheDocument()
    })
  })
})
