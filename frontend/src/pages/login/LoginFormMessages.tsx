/**
 * Login Form Messages Component
 * 
 * Error messages and informational content for the login form.
 * Extracted to maintain 100-line limit per CLAUDE.md rules.
 */

import React from 'react'
import { AlertCircle } from 'lucide-react'

interface LoginFormMessagesProps {
  submitError?: string
  authError?: string
}

export function LoginFormMessages({ submitError, authError }: LoginFormMessagesProps) {
  return (
    <>
      {/* Global Error Message */}
      {(submitError || authError) && (
        <div className="form-feedback form-feedback-error">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>{submitError || authError}</span>
          </div>
        </div>
      )}

      {/* Demo Credentials Info */}
      <div className="form-feedback form-feedback-info">
        <div className="text-sm">
          <strong>Demo Credentials:</strong>
          <div className="mt-1 space-y-1">
            <div>Admin: <code className="text-xs">admin / HomeLabAdmin123!</code></div>
            <div>User: <code className="text-xs">user / HomeLabUser123!</code></div>
          </div>
        </div>
      </div>
    </>
  )
}