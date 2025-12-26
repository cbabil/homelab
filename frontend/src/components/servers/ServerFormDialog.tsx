/**
 * Server Form Dialog Component
 * 
 * Modal dialog for adding or editing server connections.
 */

import React from 'react'
import { X } from 'lucide-react'
import { ServerConnection, ServerConnectionInput } from '@/types/server'
import { ServerBasicFields } from './ServerBasicFields'
import { AuthenticationSection } from './AuthenticationSection'
import { useServerForm } from '@/hooks/useServerForm'

interface ServerFormDialogProps {
  isOpen: boolean
  onClose: () => void
  onSave: (server: ServerConnectionInput) => void
  server?: ServerConnection
  title: string
}

export function ServerFormDialog({ 
  isOpen, 
  onClose, 
  onSave, 
  server, 
  title 
}: ServerFormDialogProps) {
  const {
    formData,
    handleInputChange,
    handleAuthTypeChange,
    handleCredentialChange
  } = useServerForm(server)

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave(formData)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background p-6 rounded-xl border max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">{title}</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-accent rounded-md"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <ServerBasicFields
            formData={formData}
            onInputChange={handleInputChange}
          />

          <AuthenticationSection
            authType={formData.auth_type}
            credentials={formData.credentials}
            onAuthTypeChange={handleAuthTypeChange}
            onCredentialChange={handleCredentialChange}
            isEditMode={!!server}
          />

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-input rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 btn-gradient px-4 py-2 rounded-lg font-medium text-sm"
            >
              {server ? 'Update' : 'Add'} Server
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}