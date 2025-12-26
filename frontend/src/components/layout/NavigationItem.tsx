/**
 * Navigation Item Component
 *
 * Individual navigation item with icon, label, badge, and sub-items support.
 * Features smooth animations, hover effects, and accessibility support.
 */

import { memo } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { cn } from '@/utils/cn'
import { NavItem, SubNavItem } from '@/hooks/useNavigation'
import { Button } from '@/components/ui/Button'

interface NavigationItemProps {
  item: NavItem
  isActive: boolean
  isExpanded?: boolean
  onToggle?: () => void
  onSubItemClick?: (subItem: SubNavItem) => void
  isActiveSubItem?: (subItem: SubNavItem) => boolean
}

export const NavigationItem = memo(({
  item,
  isActive,
  isExpanded = false,
  onToggle,
  onSubItemClick,
  isActiveSubItem
}: NavigationItemProps) => {
  const hasSubItems = item.subItems && item.subItems.length > 0
  const showBadge = item.badge !== undefined

  const handleMainClick = () => {
    if (hasSubItems && onToggle) {
      onToggle()
    }
  }

  const handleSubItemClick = (subItem: SubNavItem) => {
    if (onSubItemClick) {
      onSubItemClick(subItem)
    }
  }

  return (
    <div className="nav-item-container">
      {/* Main Navigation Item */}
      <div className="relative">
        {hasSubItems ? (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleMainClick}
            className={cn(
              'group flex items-center justify-between w-full',
              'relative overflow-hidden',
              isActive
                ? 'bg-primary text-white hover:bg-primary hover:text-white'
                : 'text-muted-foreground hover:text-white hover:bg-primary'
            )}
            title={item.description}
            aria-expanded={isExpanded}
            aria-controls={`nav-subitems-${item.id}`}
          >
            <div className="flex items-center space-x-3">
              <item.icon className="h-4 w-4 flex-shrink-0" />
              <span className="font-medium truncate">{item.label}</span>
              {showBadge && (
                <span className={cn(
                  'w-5 h-5 flex items-center justify-center text-xs font-medium rounded-full',
                  isActive
                    ? 'bg-white/20 text-white'
                    : typeof item.badge === 'number'
                    ? 'bg-destructive text-destructive-foreground group-hover:bg-white/20 group-hover:text-white'
                    : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 group-hover:bg-white/20 group-hover:text-white'
                )}>
                  {item.badge}
                </span>
              )}
            </div>
            <ChevronRight
              className={cn(
                'h-4 w-4 transition-transform duration-200',
                isActive ? 'text-white' : 'text-muted-foreground group-hover:text-white',
                isExpanded && 'rotate-90'
              )}
            />
          </Button>
        ) : (
          <Link
            to={item.href}
            className={cn(
              'group flex items-center space-x-3 px-3 py-2 rounded-md text-sm',
              'relative overflow-hidden',
              'focus:outline-none focus:ring-1 focus:ring-primary/30',
              isActive
                ? 'bg-primary text-white'
                : 'text-muted-foreground hover:text-white hover:bg-primary'
            )}
            title={item.description}
          >
            <item.icon className="h-4 w-4 flex-shrink-0" />
            <span className="font-medium truncate">{item.label}</span>
            {showBadge && (
              <span className={cn(
                'ml-auto w-5 h-5 flex items-center justify-center text-xs font-medium rounded-full',
                isActive
                  ? 'bg-white/20 text-white'
                  : typeof item.badge === 'number'
                  ? 'bg-destructive text-destructive-foreground group-hover:bg-white/20 group-hover:text-white'
                  : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 group-hover:bg-white/20 group-hover:text-white'
              )}>
                {item.badge}
              </span>
            )}
          </Link>
        )}

      </div>

      {/* Sub Navigation Items */}
      {hasSubItems && (
        <div
          id={`nav-subitems-${item.id}`}
          className={cn(
            'overflow-hidden transition-all duration-300 ease-in-out',
            isExpanded ? 'max-h-80 opacity-100' : 'max-h-0 opacity-0'
          )}
        >
          <div className="ml-4 mt-1 space-y-0.5 border-l border-border/20 pl-2">
            {item.subItems!.map((subItem) => {
              const isSubActive = isActiveSubItem?.(subItem) || false
              
              return (
                <Link
                  key={subItem.href}
                  to={subItem.href}
                  onClick={() => handleSubItemClick(subItem)}
                  className={cn(
                    'flex items-center justify-between px-2 py-1.5 rounded text-xs',
                    'focus:outline-none focus:ring-1 focus:ring-primary/30',
                    isSubActive
                      ? 'bg-primary text-white font-medium'
                      : 'text-muted-foreground hover:text-white hover:bg-primary'
                  )}
                  title={`${subItem.label}${subItem.count !== undefined ? ` (${subItem.count})` : ''}`}
                >
                  <span className="truncate">{subItem.label}</span>
                  {subItem.count !== undefined && (
                    <span className={cn(
                      'ml-1 w-5 h-5 flex items-center justify-center text-xs rounded-full flex-shrink-0',
                      isSubActive
                        ? 'bg-white/20 text-white'
                        : 'bg-muted/60 text-muted-foreground group-hover:bg-white/20 group-hover:text-white'
                    )}>
                      {subItem.count}
                    </span>
                  )}
                </Link>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
})

NavigationItem.displayName = 'NavigationItem'