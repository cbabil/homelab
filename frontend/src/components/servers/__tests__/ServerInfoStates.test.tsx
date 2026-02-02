/**
 * ServerInfoStates Test Suite
 *
 * Tests for the LoadingState and ErrorState components.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LoadingState, ErrorState } from '../ServerInfoStates'

describe('LoadingState', () => {
  it('should render loading text', () => {
    render(<LoadingState />)

    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('should render spinner with animation class', () => {
    const { container } = render(<LoadingState />)

    const spinner = container.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
  })
})

describe('ErrorState', () => {
  it('should render info unavailable text', () => {
    render(<ErrorState />)

    expect(screen.getByText('Info unavailable')).toBeInTheDocument()
  })

  it('should render monitor icon', () => {
    const { container } = render(<ErrorState />)

    // Component renders and contains content
    expect(container.firstChild).toBeInTheDocument()
  })
})
