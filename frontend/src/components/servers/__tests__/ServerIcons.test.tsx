/**
 * ServerIcons Test Suite
 *
 * Tests for the LinuxIcon and DockerIcon SVG components.
 */

import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { LinuxIcon, DockerIcon } from '../ServerIcons'

describe('LinuxIcon', () => {
  it('should render SVG element', () => {
    const { container } = render(<LinuxIcon />)

    expect(container.querySelector('svg')).toBeInTheDocument()
  })

  it('should apply className when provided', () => {
    const { container } = render(<LinuxIcon className="custom-class" />)

    expect(container.querySelector('svg')).toHaveClass('custom-class')
  })

  it('should apply custom style', () => {
    const { container } = render(<LinuxIcon style={{ width: 32, height: 32 }} />)

    const svg = container.querySelector('svg')
    expect(svg).toHaveStyle({ width: '32px', height: '32px' })
  })

  it('should have default size of 24x24', () => {
    const { container } = render(<LinuxIcon />)

    const svg = container.querySelector('svg')
    expect(svg).toHaveStyle({ width: '24px', height: '24px' })
  })
})

describe('DockerIcon', () => {
  it('should render SVG element', () => {
    const { container } = render(<DockerIcon />)

    expect(container.querySelector('svg')).toBeInTheDocument()
  })

  it('should apply className when provided', () => {
    const { container } = render(<DockerIcon className="docker-icon" />)

    expect(container.querySelector('svg')).toHaveClass('docker-icon')
  })

  it('should apply custom style', () => {
    const { container } = render(<DockerIcon style={{ width: 16, height: 16 }} />)

    const svg = container.querySelector('svg')
    expect(svg).toHaveStyle({ width: '16px', height: '16px' })
  })

  it('should have default size of 24x24', () => {
    const { container } = render(<DockerIcon />)

    const svg = container.querySelector('svg')
    expect(svg).toHaveStyle({ width: '24px', height: '24px' })
  })
})
