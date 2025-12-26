/**
 * Read-Only Private Key Display Tests
 * 
 * Tests for the read-only private key display component.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ReadOnlyPrivateKeyDisplay } from '../ReadOnlyPrivateKeyDisplay'

describe('ReadOnlyPrivateKeyDisplay', () => {
  it('renders private key configured message', () => {
    render(<ReadOnlyPrivateKeyDisplay />)
    
    expect(screen.getByText('Private Key File')).toBeInTheDocument()
    expect(screen.getByText('Private key configured')).toBeInTheDocument()
    expect(screen.getByText('Private key cannot be changed in edit mode for security reasons')).toBeInTheDocument()
  })

  it('displays lock icon', () => {
    render(<ReadOnlyPrivateKeyDisplay />)
    
    const lockIcon = screen.getByText('Private key configured').closest('div')?.querySelector('svg')
    expect(lockIcon).toBeInTheDocument()
  })

  it('has correct styling for read-only state', () => {
    render(<ReadOnlyPrivateKeyDisplay />)
    
    const container = screen.getByText('Private key configured').closest('div')?.parentElement
    expect(container).toHaveClass('cursor-not-allowed')
    expect(container).toHaveClass('bg-muted/20')
  })
})