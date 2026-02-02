/**
 * Private Key File Input Validation Tests
 * 
 * Tests for file validation and error handling functionality.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PrivateKeyFileInput } from '../PrivateKeyFileInput'
import {
  setupFileReaderMock,
  createMockFile,
  simulateFileLoad
} from '../../../test/utils/server-test-utils'

const { mockOnChange } = vi.hoisted(() => {
  const mockOnChange = vi.fn()
  return { mockOnChange }
})

setupFileReaderMock()

describe('PrivateKeyFileInput - Validation', () => {

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders file input with correct label', () => {
    render(<PrivateKeyFileInput onChange={mockOnChange} />)
    
    expect(screen.getByText('Private Key File')).toBeInTheDocument()
    expect(screen.getByText('Select private key file')).toBeInTheDocument()
  })

  it('accepts valid private key file types', () => {
    render(<PrivateKeyFileInput onChange={mockOnChange} />)
    
    const fileInput = document.getElementById('private-key-file') as HTMLInputElement
    
    expect(fileInput).toHaveAttribute('accept', '.pem,.key,.id_rsa,.openssh,.ppk')
  })

  it('validates file size and shows error for large files', async () => {
    render(<PrivateKeyFileInput onChange={mockOnChange} />)
    
    const largeFile = createMockFile('x'.repeat(11 * 1024), 'large-key.pem')
    const fileInput = document.getElementById('private-key-file') as HTMLInputElement
    
    fireEvent.change(fileInput, { target: { files: [largeFile] } })
    
    await waitFor(() => {
      expect(screen.getByText('Private key file must be less than 10KB')).toBeInTheDocument()
    })
    
    expect(mockOnChange).not.toHaveBeenCalled()
  })

  it('validates file extension and shows error for invalid files', async () => {
    render(<PrivateKeyFileInput onChange={mockOnChange} />)
    
    const invalidFile = createMockFile('content', 'invalid.txt')
    const fileInput = document.getElementById('private-key-file') as HTMLInputElement
    
    fireEvent.change(fileInput, { target: { files: [invalidFile] } })
    
    await waitFor(() => {
      expect(screen.getByText(/Please select a valid private key file/)).toBeInTheDocument()
    })
    
    expect(mockOnChange).not.toHaveBeenCalled()
  })

  it('processes valid private key file successfully', async () => {
    render(<PrivateKeyFileInput onChange={mockOnChange} />)
    
    const validKeyContent = '-----BEGIN PRIVATE KEY-----\nMIIEvQ...\n-----END PRIVATE KEY-----'
    const validFile = createMockFile(validKeyContent, 'test-key.pem')
    const fileInput = document.getElementById('private-key-file') as HTMLInputElement
    
    fireEvent.change(fileInput, { target: { files: [validFile] } })
    simulateFileLoad(validKeyContent)
    
    await waitFor(() => {
      expect(screen.getByText('File loaded successfully')).toBeInTheDocument()
    })
    
    expect(mockOnChange).toHaveBeenCalledWith(validKeyContent)
  })
})