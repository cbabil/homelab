/**
 * Marketplace App Card Component
 *
 * Clean, minimal card design matching the reference.
 * Shows icon, name, version and colored category.
 */

import { useState, useRef } from 'react'
import { createPortal } from 'react-dom'
import { Info, User, Scale, Import, Package, Wrench, Check } from 'lucide-react'
import { Card } from 'ui-toolkit'
import type { MarketplaceApp } from '@/types/marketplace'

// Category color mapping
const categoryColors: Record<string, string> = {
  networking: 'text-blue-500',
  automation: 'text-orange-500',
  media: 'text-red-500',
  security: 'text-green-500',
  monitoring: 'text-purple-500',
  storage: 'text-yellow-600',
  utility: 'text-gray-500',
  development: 'text-cyan-500',
}

interface MarketplaceAppCardProps {
  app: MarketplaceApp
  onImport?: (app: MarketplaceApp) => void
  hasUpdate?: boolean
  isImported?: boolean
}

// Check if a string is a valid image URL
function isValidIconUrl(icon: string | undefined): boolean {
  if (!icon) return false
  return icon.startsWith('http://') || icon.startsWith('https://') || icon.startsWith('data:image/')
}

export function MarketplaceAppCard({ app, onImport, hasUpdate, isImported }: MarketplaceAppCardProps) {
  const [showTooltip, setShowTooltip] = useState(false)
  const [tooltipPos, setTooltipPos] = useState({ top: 0, left: 0 })
  const [iconError, setIconError] = useState(false)
  const cardRef = useRef<HTMLDivElement>(null)

  const hasValidIcon = isValidIconUrl(app.icon) && !iconError
  const categoryColor = categoryColors[app.category.toLowerCase()] || 'text-primary'

  const handleImport = (e: React.MouseEvent) => {
    e.stopPropagation()
    e.preventDefault()
    if (onImport) {
      onImport(app)
    }
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    setTooltipPos({
      top: e.clientY + 15,
      left: Math.min(e.clientX + 15, window.innerWidth - 270)
    })
  }

  const handleMouseEnter = (e: React.MouseEvent) => {
    handleMouseMove(e)
    setShowTooltip(true)
  }

  const handleMouseLeave = () => {
    setShowTooltip(false)
  }

  return (
    <Card
      ref={cardRef}
      padding="none"
      elevation="sm"
      className="relative flex flex-col items-center group p-2 h-[100px]"
      onMouseEnter={handleMouseEnter}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* Top right: Status + Import */}
      <div className="absolute top-1 right-1 flex items-center gap-0.5 z-10">
        {hasUpdate && (
          <span className="text-[7px] px-1 rounded bg-green-500/20 text-green-500 font-medium">
            UPD
          </span>
        )}
        {isImported ? (
          <Check className="h-3 w-3 text-green-500" />
        ) : (
          <button
            type="button"
            onClick={handleImport}
            className="p-0.5 rounded hover:bg-muted/50 transition-colors cursor-pointer opacity-0 group-hover:opacity-100"
            title="Import to Applications"
          >
            <Import className="h-3 w-3 text-muted-foreground hover:text-primary transition-colors" />
          </button>
        )}
      </div>

      {/* Icon */}
      <div className="w-8 h-8 flex items-center justify-center mt-1">
        {hasValidIcon ? (
          <img
            src={app.icon}
            alt=""
            className="w-8 h-8 object-contain"
            onError={() => setIconError(true)}
            onLoad={(e) => {
              const img = e.target as HTMLImageElement
              if (img.naturalWidth === 0) setIconError(true)
            }}
          />
        ) : (
          <Package className="h-6 w-6 text-muted-foreground" />
        )}
      </div>

      {/* Name */}
      <p className="text-[11px] font-medium truncate w-full text-center mt-1.5 px-1">{app.name}</p>

      {/* Version */}
      <p className="text-[9px] text-muted-foreground">v{app.version}</p>

      {/* Category */}
      <p className={`text-[9px] font-medium ${categoryColor}`}>{app.category}</p>

      {/* Tooltip */}
      {showTooltip && createPortal(
        <div
          className="fixed w-64 bg-popover border border-border rounded-lg shadow-lg z-[9999] overflow-hidden pointer-events-none"
          style={{ top: tooltipPos.top, left: tooltipPos.left }}
        >
          <div className="p-3 border-b border-border">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 flex items-center justify-center">
                {hasValidIcon ? (
                  <img src={app.icon} alt="" className="w-8 h-8 object-contain" />
                ) : (
                  <Package className="h-5 w-5 text-muted-foreground" />
                )}
              </div>
              <div>
                <h4 className="font-semibold text-sm">{app.name}</h4>
                <p className="text-xs text-muted-foreground">v{app.version}</p>
              </div>
            </div>
          </div>

          <div className="p-3 space-y-2 text-xs">
            <div className="flex items-center gap-2">
              <User className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-muted-foreground">Author</span>
              <span className="ml-auto font-medium">{app.author || '—'}</span>
            </div>
            <div className="flex items-center gap-2">
              <Scale className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-muted-foreground">License</span>
              <span className="ml-auto font-medium">{app.license || '—'}</span>
            </div>
            <div className="flex items-center gap-2">
              <Wrench className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-muted-foreground">Maintainer</span>
              <span className="ml-auto font-medium">{app.maintainers?.join(', ') || '—'}</span>
            </div>
          </div>

          {app.description && (
            <div className="p-3 bg-muted/50 border-t border-border">
              <p className="text-xs text-muted-foreground">{app.description}</p>
            </div>
          )}
        </div>,
        document.body
      )}
    </Card>
  )
}
