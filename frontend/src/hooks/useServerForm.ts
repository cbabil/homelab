/**
 * Server Form Hook
 * 
 * Custom hook for managing server form state and handlers.
 */

import { useState, useEffect } from 'react'
import { ServerConnection, ServerConnectionInput, AuthType } from '@/types/server'

export function useServerForm(server?: ServerConnection) {
  const [formData, setFormData] = useState<ServerConnectionInput>({
    name: '',
    host: '',
    port: 22,
    username: '',
    auth_type: 'password',
    credentials: {}
  })

  useEffect(() => {
    if (server) {
      setFormData({
        name: server.name,
        host: server.host,
        port: server.port,
        username: server.username,
        auth_type: server.auth_type,
        credentials: {
          // For private key auth, indicate existing key without exposing content
          ...(server.auth_type === 'key' && { private_key: '***EXISTING_KEY***' })
        }
      })
    } else {
      setFormData({
        name: '',
        host: '',
        port: 22,
        username: '',
        auth_type: 'password',
        credentials: {}
      })
    }
  }, [server])

  const handleInputChange = (field: string, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleAuthTypeChange = (authType: AuthType) => {
    setFormData(prev => ({ ...prev, auth_type: authType, credentials: {} }))
  }

  const handleCredentialChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      credentials: { ...prev.credentials, [field]: value }
    }))
  }

  return {
    formData,
    handleInputChange,
    handleAuthTypeChange,
    handleCredentialChange
  }
}