/**
 * Navigation Sidebar Component
 *
 * Uses MUI List components for consistent navigation with
 * real-time stats and marketplace footer. Supports expandable submenus.
 */

import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ShoppingCart, ChevronDown, ChevronRight, LucideIcon } from 'lucide-react'
import {
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Badge,
  Box,
  Collapse
} from '@mui/material'
import { useNavigation } from '@/hooks/useNavigation'
import { QuickStats } from './QuickStats'

interface SubItemType {
  href: string
  label: string
  icon?: LucideIcon
  count?: number
}

interface SubMenuListProps {
  subItems: SubItemType[]
  isSubItemActive: (href: string) => boolean
  onSelect: (href: string) => void
}

function SubMenuList({ subItems, isSubItemActive, onSelect }: SubMenuListProps) {
  return (
    <List dense disablePadding>
      {subItems.map((subItem) => (
        <ListItem key={subItem.href} disablePadding>
          <ListItemButton
            selected={isSubItemActive(subItem.href)}
            onClick={() => onSelect(subItem.href)}
            sx={{ py: 0.75, pl: 5, pr: 2 }}
          >
            {subItem.icon && (
              <ListItemIcon sx={{ minWidth: 28 }}>
                <subItem.icon size={14} />
              </ListItemIcon>
            )}
            <ListItemText
              primary={subItem.label}
              primaryTypographyProps={{ variant: 'body2', fontSize: '0.8125rem' }}
            />
            {subItem.count !== undefined && (
              <Typography variant="caption" color="text.secondary">
                {subItem.count}
              </Typography>
            )}
          </ListItemButton>
        </ListItem>
      ))}
    </List>
  )
}

export function Navigation() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const { stats, navigationItems: navData, shouldExpand } = useNavigation()
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {}
    navData.forEach(item => {
      if (item.parentOnly && item.subItems) {
        initial[item.id] = shouldExpand(item)
      }
    })
    return initial
  })

  const handleSelect = (value: string) => navigate(value)

  const handleToggleExpand = (itemId: string) => {
    setExpandedItems(prev => ({ ...prev, [itemId]: !prev[itemId] }))
  }

  const isSubItemActive = (href: string) => location.pathname === href

  const isParentActive = (item: typeof navData[0]) => {
    if (item.subItems) {
      return item.subItems.some(sub => location.pathname === sub.href)
    }
    return location.pathname === item.href
  }

  const handleItemClick = (item: typeof navData[0]) => {
    if (item.parentOnly && item.subItems && !item.alwaysExpanded) {
      handleToggleExpand(item.id)
    } else if (!item.parentOnly || !item.alwaysExpanded) {
      handleSelect(item.href)
    }
  }

  return (
    <Box
      component="aside"
      sx={{
        width: 256,
        borderRight: 1,
        borderColor: 'divider',
        bgcolor: 'background.default',
        display: 'flex',
        flexDirection: 'column',
        height: '100%'
      }}
    >
      <Box sx={{ px: 2, py: 1.5 }}>
        <Typography variant="caption" color="text.secondary" fontWeight={600}>
          {t('nav.navigation', 'Navigation')}
        </Typography>
      </Box>
      <List dense disablePadding>
        {navData.map((item) => (
          <Box key={item.id}>
            <ListItem disablePadding>
              <ListItemButton
                selected={!item.parentOnly && location.pathname === item.href}
                onClick={() => handleItemClick(item)}
                sx={{
                  py: 1,
                  px: 2,
                  ...(item.parentOnly && isParentActive(item) && { color: 'primary.main' }),
                  ...(item.parentOnly && item.subItems && {
                    '&:hover': { bgcolor: 'transparent' },
                    cursor: 'pointer'
                  })
                }}
              >
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <item.icon size={16} />
                </ListItemIcon>
                <ListItemText primary={item.label} primaryTypographyProps={{ variant: 'body2' }} />
                {item.badge !== undefined && (
                  <Badge badgeContent={item.badge} color="error" sx={{ ml: 1 }} />
                )}
                {item.parentOnly && item.subItems && !item.alwaysExpanded && (
                  expandedItems[item.id] ? <ChevronDown size={16} /> : <ChevronRight size={16} />
                )}
              </ListItemButton>
            </ListItem>
            {item.parentOnly && item.subItems && (
              item.alwaysExpanded ? (
                <SubMenuList
                  subItems={item.subItems}
                  isSubItemActive={isSubItemActive}
                  onSelect={handleSelect}
                />
              ) : (
                <Collapse in={expandedItems[item.id]} timeout="auto" unmountOnExit>
                  <SubMenuList
                    subItems={item.subItems}
                    isSubItemActive={isSubItemActive}
                    onSelect={handleSelect}
                  />
                </Collapse>
              )
            )}
          </Box>
        ))}
      </List>

      <Box sx={{ flex: 1 }} />

      <QuickStats stats={stats} />

      <Box sx={{ px: 2, pb: 2 }}>
        <List dense disablePadding>
          <ListItem disablePadding>
            <ListItemButton
              selected={location.pathname === '/marketplace'}
              onClick={() => handleSelect('/marketplace')}
              sx={{ py: 1, px: 2 }}
            >
              <ListItemIcon sx={{ minWidth: 32 }}>
                <ShoppingCart size={16} />
              </ListItemIcon>
              <ListItemText
                primary={t('nav.marketplace')}
                primaryTypographyProps={{ variant: 'body2' }}
              />
            </ListItemButton>
          </ListItem>
        </List>
      </Box>
    </Box>
  )
}
