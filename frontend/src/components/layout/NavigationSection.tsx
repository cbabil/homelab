/**
 * Navigation Section Component
 * 
 * Grouping component for navigation items with optional header and dividers.
 * Supports collapsible sections and improved visual organization.
 */

import { memo, ReactNode } from 'react'
import { cn } from '@/utils/cn'

interface NavigationSectionProps {
  title?: string
  children: ReactNode
  className?: string
  collapsible?: boolean
  isCollapsed?: boolean
  onToggle?: () => void
  showDivider?: boolean
}

export const NavigationSection = memo(({
  title,
  children,
  className,
  collapsible = false,
  isCollapsed = false,
  onToggle,
  showDivider = false
}: NavigationSectionProps) => {
  return (
    <div className={cn('nav-section', className)}>
      {showDivider && (
        <div className="mx-3 my-4 border-t border-border/50" />
      )}
      
      {title && (
        <div className="px-3 mb-2">
          {collapsible ? (
            <button
              onClick={onToggle}
              className={cn(
                'flex items-center justify-between w-full px-2 py-1 rounded-md',
                'text-xs font-semibold text-muted-foreground uppercase tracking-wider',
                'hover:text-foreground transition-colors duration-200',
                'focus:outline-none focus:ring-2 focus:ring-primary/20'
              )}
              aria-expanded={!isCollapsed}
              aria-controls={`nav-section-${title.toLowerCase().replace(/\s+/g, '-')}`}
            >
              <span>{title}</span>
              <svg
                className={cn(
                  'h-3 w-3 transition-transform duration-200',
                  isCollapsed && 'rotate-180'
                )}
                viewBox="0 0 12 12"
                fill="currentColor"
              >
                <path d="M6 8L2 4h8l-4 4z" />
              </svg>
            </button>
          ) : (
            <h3 className="px-2 py-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              {title}
            </h3>
          )}
        </div>
      )}
      
      <div
        id={title ? `nav-section-${title.toLowerCase().replace(/\s+/g, '-')}` : undefined}
        className={cn(
          'space-y-1',
          collapsible && (isCollapsed 
            ? 'max-h-0 overflow-hidden opacity-0 transition-all duration-300 ease-in-out'
            : 'max-h-none opacity-100 transition-all duration-300 ease-in-out'
          )
        )}
      >
        {children}
      </div>
    </div>
  )
})

NavigationSection.displayName = 'NavigationSection'