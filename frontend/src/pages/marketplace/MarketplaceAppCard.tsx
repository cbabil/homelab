/**
 * Marketplace App Card Component
 *
 * Card component for displaying marketplace apps with:
 * - App icon (placeholder if none)
 * - App name and version
 * - Description (truncated to 2 lines)
 * - Category badge
 * - Star rating display
 * - Install/View button
 * - Featured badge (if featured)
 */

import { Star, Download } from 'lucide-react'
import type { MarketplaceApp } from '@/types/marketplace'

interface MarketplaceAppCardProps {
  app: MarketplaceApp
  onInstall?: (app: MarketplaceApp) => void
}

export function MarketplaceAppCard({ app, onInstall }: MarketplaceAppCardProps) {
  const handleInstall = () => {
    if (onInstall) {
      onInstall(app)
    } else {
      console.log('Install app:', app.name)
    }
  }

  return (
    <div className="card-app">
      <div className="flex-1 space-y-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start space-x-2 min-w-0 flex-1">
            {/* App Icon */}
            <div className="w-9 h-9 rounded-md bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0 overflow-hidden">
              {app.icon ? (
                <img
                  src={app.icon}
                  alt={app.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <span className="text-gray-400 dark:text-gray-600 text-base font-semibold">
                  {app.name.charAt(0).toUpperCase()}
                </span>
              )}
            </div>

            {/* App Name and Description */}
            <div className="space-y-0.5 min-w-0 flex-1">
              <h3 className="font-semibold text-sm leading-tight truncate">
                {app.name}
              </h3>
              <p className="text-xs text-muted-foreground line-clamp-2">
                {app.description}
              </p>
            </div>
          </div>

          {/* Featured Badge */}
          {app.featured && (
            <div className="flex items-center space-x-0.5 px-1 py-0.5 rounded bg-yellow-100 dark:bg-yellow-900/50 text-yellow-700 dark:text-yellow-300 text-xs font-medium shrink-0">
              <Star className="h-2.5 w-2.5 fill-current" />
            </div>
          )}
        </div>

        {/* Metadata Row */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center space-x-2">
            {/* Rating Display */}
            {app.avgRating !== undefined && app.avgRating !== null && (
              <div className="flex items-center space-x-0.5">
                <Star className="h-3 w-3 fill-current text-yellow-500" />
                <span>{app.avgRating.toFixed(1)}</span>
                {app.ratingCount > 0 && (
                  <span className="text-muted-foreground">
                    ({app.ratingCount})
                  </span>
                )}
              </div>
            )}

            {/* Install Count */}
            {app.installCount > 0 && (
              <div className="flex items-center space-x-0.5">
                <Download className="h-3 w-3" />
                <span>
                  {app.installCount > 999
                    ? `${Math.round(app.installCount / 1000)}k`
                    : app.installCount}
                </span>
              </div>
            )}
          </div>

          {/* Version Badge */}
          <span className="px-1.5 py-0.5 rounded bg-accent text-xs font-medium">
            v{app.version}
          </span>
        </div>

        {/* Category and Tags */}
        <div className="flex flex-wrap gap-1">
          {/* Category Badge */}
          <span className="px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 text-xs font-medium">
            {app.category}
          </span>

          {/* Tags (show up to 2) */}
          {app.tags.slice(0, 2).map((tag) => (
            <span
              key={tag}
              className="px-1.5 py-0.5 rounded bg-secondary text-secondary-foreground text-xs font-medium"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* Install Button */}
      <div className="flex items-center space-x-1.5 pt-2">
        <button
          onClick={handleInstall}
          className="flex-1 btn-gradient px-2 py-1 rounded font-medium text-xs hover:opacity-90 transition-opacity"
        >
          Install
        </button>
      </div>
    </div>
  )
}
