/**
 * Private Key File Input Existing Key Tests
 * 
 * Tests for existing key handling and replacement functionality.
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

describe('PrivateKeyFileInput - Existing Key Handling', () => {

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows existing key indicator when editing server with private key', () => {
    render(<PrivateKeyFileInput value="***EXISTING_KEY***" onChange={mockOnChange} />)
    
    expect(screen.getByText('Private key configured')).toBeInTheDocument()
    expect(screen.getByText('Select a new file to replace the existing private key')).toBeInTheDocument()
    expect(screen.getByText('Select private key file')).toBeInTheDocument()
  })

  it('replaces existing key when new file is selected', async () => {
    render(<PrivateKeyFileInput value="***EXISTING_KEY***" onChange={mockOnChange} />)
    
    // Initially shows existing key indicator
    expect(screen.getByText('Private key configured')).toBeInTheDocument()
    
    // Select a new file
    const validKeyContent = '-----BEGIN PRIVATE KEY-----\nNEW_KEY...\n-----END PRIVATE KEY-----'
    const validFile = createMockFile(validKeyContent, 'new-key.pem')
    const fileInput = document.getElementById('private-key-file') as HTMLInputElement
    
    fireEvent.change(fileInput, { target: { files: [validFile] } })
    simulateFileLoad(validKeyContent)
    
    await waitFor(() => {
      expect(screen.getByText('New file loaded successfully')).toBeInTheDocument()
    })
    
    // Existing key indicator should be gone
    expect(screen.queryByText('Private key configured')).not.toBeInTheDocument()
    expect(mockOnChange).toHaveBeenCalledWith(validKeyContent)
  })
})