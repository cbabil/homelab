/**
 * Navigation Item Component
 *
 * Individual navigation item with icon, label, badge, and sub-items support.
 * Features smooth animations, hover effects, and accessibility support.
 */

import { memo } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { Box, SxProps, Theme } from '@mui/material'
import { NavItem, SubNavItem } from '@/hooks/useNavigation'

interface NavigationItemProps {
  item: NavItem
  isActive: boolean
  isExpanded?: boolean
  onToggle?: () => void
  onSubItemClick?: (subItem: SubNavItem) => void
  isActiveSubItem?: (subItem: SubNavItem) => boolean
}

interface BadgeProps {
  badge: number | string
  isActive: boolean
  isInGroup?: boolean
}

const getBadgeStyles = (isActive: boolean, badge: number | string): SxProps<Theme> => {
  if (isActive) {
    return { bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'white' }
  }
  if (typeof badge === 'number') {
    return {
      bgcolor: 'hsl(var(--destructive))',
      color: 'hsl(var(--destructive-foreground))',
      '.group:hover &': { bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'white' }
    }
  }
  return {
    bgcolor: 'warning.light',
    color: 'warning.dark',
    '.group:hover &': { bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'white' }
  }
}

const NavigationBadge = ({ badge, isActive, isInGroup = true }: BadgeProps) => (
  <Box
    component="span"
    sx={{
      ...(isInGroup ? {} : { ml: 'auto' }),
      width: 20,
      height: 20,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '0.75rem',
      fontWeight: 500,
      borderRadius: '50%',
      ...getBadgeStyles(isActive, badge)
    }}
  >
    {badge}
  </Box>
)

interface SubItemBadgeProps {
  count: number
  isActive: boolean
}

const SubItemBadge = ({ count, isActive }: SubItemBadgeProps) => (
  <Box
    component="span"
    className={isActive ? '' : 'group-hover:bg-white/20 group-hover:text-white'}
    sx={{
      ml: 0.5,
      width: 20,
      height: 20,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '0.75rem',
      borderRadius: '50%',
      flexShrink: 0,
      ...(isActive
        ? { bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'white' }
        : { bgcolor: 'hsl(var(--muted) / 0.6)', color: 'hsl(var(--muted-foreground))' })
    }}
  >
    {count}
  </Box>
)

interface SubNavigationItemProps {
  subItem: SubNavItem
  isActive: boolean
  onClick: () => void
}

const SubNavigationItemLink = ({ subItem, isActive, onClick }: SubNavigationItemProps) => (
  <Box
    component={Link}
    to={subItem.href}
    onClick={onClick}
    className={isActive ? 'bg-primary text-white' : 'text-muted-foreground hover:text-white hover:bg-primary'}
    sx={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      px: 1,
      py: 0.75,
      borderRadius: 0.5,
      fontSize: '0.75rem',
      textDecoration: 'none',
      fontWeight: isActive ? 500 : 400,
      '&:focus': {
        outline: 'none',
        boxShadow: '0 0 0 1px hsl(var(--primary) / 0.3)'
      }
    }}
    title={`${subItem.label}${subItem.count !== undefined ? ` (${subItem.count})` : ''}`}
  >
    <Box component="span" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
      {subItem.label}
    </Box>
    {subItem.count !== undefined && <SubItemBadge count={subItem.count} isActive={isActive} />}
  </Box>
)

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
    <Box>
      {/* Main Navigation Item */}
      <Box sx={{ position: 'relative' }}>
        {hasSubItems ? (
          <Box
            component="button"
            onClick={handleMainClick}
            title={item.description}
            aria-expanded={isExpanded}
            aria-controls={`nav-subitems-${item.id}`}
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              width: '100%',
              px: 1.5,
              py: 1,
              border: 'none',
              bgcolor: 'transparent !important',
              color: 'hsl(var(--muted-foreground))',
              fontSize: '0.875rem',
              cursor: 'pointer',
              borderRadius: 1,
              '&:hover': {
                bgcolor: 'transparent !important',
                background: 'transparent !important'
              },
              '&:focus': { outline: 'none' }
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <item.icon style={{ width: 16, height: 16, flexShrink: 0 }} />
              <Box component="span" sx={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {item.label}
              </Box>
              {showBadge && <NavigationBadge badge={item.badge!} isActive={isActive} />}
            </Box>
            <ChevronRight
              style={{
                width: 16,
                height: 16,
                transition: 'transform 0.2s',
                transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                color: 'hsl(var(--muted-foreground))'
              }}
            />
          </Box>
        ) : (
          <Box
            component={Link}
            to={item.href}
            className={`group ${isActive ? 'bg-primary text-white' : 'text-muted-foreground hover:text-white hover:bg-primary'}`}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1.5,
              px: 1.5,
              py: 1,
              borderRadius: 1,
              fontSize: '0.875rem',
              position: 'relative',
              overflow: 'hidden',
              textDecoration: 'none',
              '&:focus': {
                outline: 'none',
                boxShadow: '0 0 0 1px hsl(var(--primary) / 0.3)'
              }
            }}
            title={item.description}
          >
            <item.icon style={{ width: 16, height: 16, flexShrink: 0 }} />
            <Box component="span" sx={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {item.label}
            </Box>
            {showBadge && <NavigationBadge badge={item.badge!} isActive={isActive} isInGroup={false} />}
          </Box>
        )}
      </Box>

      {/* Sub Navigation Items */}
      {hasSubItems && (
        <Box
          id={`nav-subitems-${item.id}`}
          sx={{
            overflow: 'hidden',
            transition: 'all 0.3s ease-in-out',
            maxHeight: isExpanded ? 320 : 0,
            opacity: isExpanded ? 1 : 0
          }}
        >
          <Box sx={{ ml: 2, mt: 0.5, display: 'flex', flexDirection: 'column', gap: 0.25, borderLeft: 1, borderColor: 'rgba(var(--border-rgb), 0.2)', pl: 1 }}>
            {item.subItems!.map((subItem) => (
              <SubNavigationItemLink
                key={subItem.href}
                subItem={subItem}
                isActive={isActiveSubItem?.(subItem) || false}
                onClick={() => handleSubItemClick(subItem)}
              />
            ))}
          </Box>
        </Box>
      )}
    </Box>
  )
})

NavigationItem.displayName = 'NavigationItem'
