/**
 * Test Utilities for Server Components
 * 
 * Common test utilities and mocks for server-related components.
 */

import { vi } from 'vitest'

// Mock FileReader for file upload tests  
export const mockFileReader = {
  readAsText: vi.fn(),
  onload: null as unknown,
  onerror: null as unknown,
  result: null as unknown
}

export function setupFileReaderMock() {
  Object.defineProperty(globalThis, 'FileReader', {
    writable: true,
    value: vi.fn().mockImplementation(() => mockFileReader)
  })
}

export function createMockFile(content: string, name: string, type = 'text/plain') {
  return new File([content], name, { type })
}

export function simulateFileLoad(content: string) {
  mockFileReader.result = content
  setTimeout(() => {
    mockFileReader.onload?.()
  }, 0)
}