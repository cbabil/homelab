/**
 * Application Card Component
 *
 * Individual application card with deploy/manage actions.
 */

import { useState } from 'react'
import { Download, Trash2, Check, Package, Square, CheckSquare } from 'lucide-react'
import { Card } from 'ui-toolkit'
import { App } from '@/types/app'

// Check if a string is a valid image URL
function isValidIconUrl(icon: string | undefined): boolean {
  if (!icon) return false
  return icon.startsWith('http://') || icon.startsWith('https://') || icon.startsWith('data:image/')
}

interface AppCardProps {
  app: App
  isSelected?: boolean
  onToggleSelect?: (appId: string) => void
  onUninstall?: (appId: string, serverId?: string) => void
  onDeploy?: (appId: string) => void
}

export function AppCard({ app, isSelected = false, onToggleSelect, onUninstall, onDeploy }: AppCardProps) {
  const [iconError, setIconError] = useState(false)

  const handleDeploy = () => {
    if (onDeploy) {
      onDeploy(app.id)
    }
  }

  const handleUninstall = () => {
    if (onUninstall) {
      onUninstall(app.id, app.connectedServerId ?? undefined)
    }
  }

  const isInstalled = app.status === 'installed'
  const hasValidIcon = isValidIconUrl(app.icon) && !iconError
  const canSelect = onToggleSelect !== undefined

  return (
    <Card
      padding="none"
      elevation="sm"
      className={`relative flex flex-col items-center justify-center group aspect-square mt-0.5 p-1.5 ${isSelected ? 'ring-2 ring-primary' : ''}`}
    >
      {/* Top right: Selection checkbox + Status + Actions */}
      <div className="absolute top-0.5 right-0.5 flex items-center gap-0.5 z-10">
        {canSelect && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              onToggleSelect(app.id)
            }}
            className="p-0.5 rounded hover:bg-muted/50 transition-colors cursor-pointer"
            title={isSelected ? 'Deselect' : 'Select for removal'}
          >
            {isSelected ? (
              <CheckSquare className="h-3 w-3 text-primary" />
            ) : (
              <Square className="h-3 w-3 text-muted-foreground hover:text-primary transition-colors" />
            )}
          </button>
        )}
        {isInstalled ? (
          <>
            <Check className="h-3 w-3 text-green-500" />
            <button
              type="button"
              onClick={handleUninstall}
              className="p-0.5 rounded hover:bg-red-500/10 transition-colors cursor-pointer"
              title="Uninstall"
            >
              <Trash2 className="h-3 w-3 text-muted-foreground hover:text-red-500 transition-colors" />
            </button>
          </>
        ) : (
          <button
            type="button"
            onClick={handleDeploy}
            className="p-0.5 rounded hover:bg-muted/50 transition-colors cursor-pointer"
            title="Deploy"
          >
            <Download className="h-3 w-3 text-muted-foreground hover:text-primary transition-colors" />
          </button>
        )}
      </div>

      {/* Icon */}
      <div className="w-7 h-7 rounded-md bg-muted/50 border border-border/50 flex items-center justify-center mx-auto p-0.5">
        {hasValidIcon ? (
          <img
            src={app.icon}
            alt=""
            className="w-full h-full object-contain"
            onError={() => setIconError(true)}
            onLoad={(e) => {
              const img = e.target as HTMLImageElement
              if (img.naturalWidth === 0) setIconError(true)
            }}
          />
        ) : (
          <Package className="h-3.5 w-3.5 text-muted-foreground" />
        )}
      </div>

      {/* Name */}
      <p className="text-[10px] font-medium truncate w-full text-center mt-0.5">{app.name}</p>

      {/* Footer: Version + Category */}
      <div className="flex items-center justify-between mt-0.5">
        <span className="text-[8px] text-muted-foreground">v{app.version}</span>
        <span className="text-[8px] px-1 py-0.5 rounded-full bg-primary/10 text-primary">{app.category.name}</span>
      </div>
    </Card>
  )
}