/**
 * Read-Only Private Key Display Component
 * 
 * Shows private key status in edit mode without allowing changes.
 */

import { Lock } from 'lucide-react'

export function ReadOnlyPrivateKeyDisplay() {
  return (
    <div>
      <label className="block text-sm font-medium mb-1">Private Key File</label>
      
      <div className="w-full px-3 py-2 border border-input rounded-lg bg-muted/20 
                      flex items-center justify-center cursor-not-allowed">
        <div className="flex items-center space-x-2 text-muted-foreground">
          <Lock className="h-4 w-4" />
          <span className="text-sm">Private key configured</span>
        </div>
      </div>
      
      <p className="mt-2 text-xs text-muted-foreground">
        Private key cannot be changed in edit mode for security reasons
      </p>
    </div>
  )
}