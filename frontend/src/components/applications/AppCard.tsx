/**
 * Application Card Component
 * 
 * Individual application card with install/manage actions.
 */

import { Star, Download, Trash2 } from 'lucide-react'
import { App } from '@/types/app'
import { cn } from '@/utils/cn'
// Generic component styles now imported globally

interface AppCardProps {
  app: App
}

export function AppCard({ app }: AppCardProps) {
  const handleUninstall = () => {
    console.log('Uninstall app:', app.name)
  }

  return (
    <div
      className="card-app"
    >
      <div className="flex-1 space-y-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start space-x-2 min-w-0 flex-1">
            <div className={cn("p-1 rounded-md shrink-0", app.category.color)}>
              {(() => {
                const Icon = app.category.icon
                return <Icon className="h-3.5 w-3.5" />
              })()}
            </div>
            <div className="space-y-0.5 min-w-0 flex-1">
              <h3 className="font-semibold text-sm leading-tight truncate">{app.name}</h3>
              <p className="text-xs text-muted-foreground line-clamp-2">{app.description}</p>
            </div>
          </div>
          
          {app.featured && (
            <div className="flex items-center space-x-0.5 px-1 py-0.5 rounded bg-yellow-100 dark:bg-yellow-900/50 text-yellow-700 dark:text-yellow-300 text-xs font-medium shrink-0">
              <Star className="h-2.5 w-2.5 fill-current" />
            </div>
          )}
        </div>

        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-0.5">
              <Star className="h-3 w-3 fill-current text-yellow-500" />
              <span>{app.rating}</span>
            </div>
            
            <div className="flex items-center space-x-0.5">
              <Download className="h-3 w-3" />
              <span>{(app.installCount || 0) > 999 ? `${Math.round((app.installCount || 0) / 1000)}k` : (app.installCount || 0)}</span>
            </div>
          </div>
          
          <span className="px-1.5 py-0.5 rounded bg-accent text-xs font-medium">
            v{app.version}
          </span>
        </div>

        <div className="flex flex-wrap gap-1">
          {app.tags.slice(0, 2).map(tag => (
            <span
              key={tag}
              className="px-1.5 py-0.5 rounded bg-secondary text-secondary-foreground text-xs font-medium"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      <div className="flex items-center space-x-1.5 pt-2">
        {app.status === 'installed' ? (
          <>
            <button className="flex-1 flex items-center justify-center px-2 py-1 bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300 rounded text-xs font-medium">
              Installed
            </button>
            <button 
              onClick={handleUninstall}
              className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/50 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors" 
              title="Uninstall"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </>
        ) : (
          <button className="flex-1 btn-gradient px-2 py-1 rounded font-medium text-xs hover:opacity-90 transition-opacity">
            Install
          </button>
        )}
      </div>
    </div>
  )
}