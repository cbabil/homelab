/**
 * Server Info States Component
 * 
 * Loading and error state components for server information display.
 */

import { Loader2, Monitor } from 'lucide-react'

export function LoadingState() {
  return (
    <div className="flex items-center justify-center py-4 space-x-2">
      <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
      <span className="text-xs text-muted-foreground">Loading...</span>
    </div>
  )
}

export function ErrorState() {
  return (
    <div className="flex items-center justify-center py-3">
      <div className="text-center space-y-1">
        <Monitor className="h-4 w-4 mx-auto text-muted-foreground/50" />
        <p className="text-xs text-muted-foreground">Info unavailable</p>
      </div>
    </div>
  )
}