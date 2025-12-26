/**
 * Authentication Type Selector Component
 * 
 * Radio button selection for authentication method.
 */

import { AuthType } from '@/types/server'

interface AuthTypeSelectorProps {
  authType: AuthType
  onAuthTypeChange: (authType: AuthType) => void
}

export function AuthTypeSelector({ 
  authType, 
  onAuthTypeChange 
}: AuthTypeSelectorProps) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1">Authentication</label>
      <div className="flex space-x-4">
        <label className="flex items-center">
          <input
            type="radio"
            value="password"
            checked={authType === 'password'}
            onChange={(e) => onAuthTypeChange(e.target.value as AuthType)}
            className="mr-2"
          />
          Password
        </label>
        <label className="flex items-center">
          <input
            type="radio"
            value="key"
            checked={authType === 'key'}
            onChange={(e) => onAuthTypeChange(e.target.value as AuthType)}
            className="mr-2"
          />
          Private Key
        </label>
      </div>
    </div>
  )
}