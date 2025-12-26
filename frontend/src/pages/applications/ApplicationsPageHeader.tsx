/**
 * Applications Page Header Component
 * 
 * Header section with title, description, and Add App button for the Applications page.
 */

import { Plus } from 'lucide-react'

interface ApplicationsPageHeaderProps {
  onAddApp: () => void
}

export function ApplicationsPageHeader({ onAddApp }: ApplicationsPageHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex-1 min-w-0">
        <h1 className="text-xl font-bold tracking-tight">Application Marketplace</h1>
        <p className="text-muted-foreground text-xs truncate">
          Discover and install applications for your homelab infrastructure.
        </p>
      </div>
      
      <button 
        onClick={onAddApp}
        className="btn-gradient flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-medium text-sm hover:opacity-90 transition-opacity shrink-0 ml-3"
      >
        <Plus className="h-3.5 w-3.5" />
        <span>Add App</span>
      </button>
    </div>
  )
}