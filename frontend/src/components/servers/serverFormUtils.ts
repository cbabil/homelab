/**
 * Server Form Utilities
 *
 * Non-component helper functions and hooks for ServerFormDialog.
 */

import { useState, useEffect } from 'react'
import { ServerConnectionInput } from '@/types/server'

export function parseHostPort(
  value: string,
  onPortChange: (port: number) => void
): string {
  if (value.includes(':')) {
    const [host, portStr] = value.split(':')
    const port = parseInt(portStr)
    if (!isNaN(port) && port > 0 && port <= 65535) onPortChange(port)
    return host
  }
  return value
}

export function canSubmitForm(
  formData: ServerConnectionInput,
  hasExistingKey: boolean
): boolean {
  return !!(
    formData.name &&
    formData.host &&
    formData.username &&
    ((formData.auth_type === 'password' && formData.credentials.password) ||
      (formData.auth_type === 'key' && formData.credentials.private_key) ||
      hasExistingKey)
  )
}

export function useAnimatedDots(isAnimating: boolean) {
  const [dots, setDots] = useState('.')
  useEffect(() => {
    if (!isAnimating) return
    const interval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? '.' : prev + '.'))
    }, 400)
    return () => clearInterval(interval)
  }, [isAnimating])
  return dots
}
