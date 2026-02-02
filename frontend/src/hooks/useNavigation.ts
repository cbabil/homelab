/**
 * Navigation Hook
 * 
 * Centralized navigation state management and utility functions.
 * Provides active state detection, navigation items, and counts.
 */

import { useLocation } from 'react-router-dom'
import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Home, Server, Package, FileText, Shield, ScrollText, type LucideIcon } from 'lucide-react'
import { useApplications } from '@/hooks/useApplications'

export interface SubNavItem {
  label: string
  href: string
  count?: number
  icon?: LucideIcon
}

export interface NavItem {
  id: string
  label: string
  href: string
  icon: LucideIcon
  description: string
  subItems?: SubNavItem[]
  badge?: number | string
  /** If true, parent item is not clickable - only subItems are navigable */
  parentOnly?: boolean
  /** If true, submenu is always visible (no collapse) */
  alwaysExpanded?: boolean
}

export interface NavigationStats {
  totalServers: number
  connectedServers: number
  totalApps: number
  installedApps: number
  criticalAlerts: number
}

export function useNavigation() {
  const { t } = useTranslation()
  const location = useLocation()
  const { apps } = useApplications()

  // Calculate app counts
  const appCounts = useMemo(() => {
    const totalApps = apps.length
    const installedApps = apps.filter(app => app.status === 'installed').length
    const categoryCounts = apps.reduce((acc, app) => {
      acc[app.category.id] = (acc[app.category.id] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    return { totalApps, installedApps, categoryCounts }
  }, [apps])

  // Server stats - actual counts come from useServers in ServersPage
  // Navigation just shows badge when there are disconnected servers
  const serverStats = useMemo(() => {
    // Stats are managed by useServers hook, navigation doesn't fetch servers
    return { totalServers: 0, connectedServers: 0 }
  }, [])

  // Combined stats 
  const stats: NavigationStats = useMemo(() => ({
    totalServers: serverStats.totalServers,
    connectedServers: serverStats.connectedServers,
    totalApps: appCounts.totalApps,
    installedApps: appCounts.installedApps,
    criticalAlerts: apps.filter(app => app.status === 'error').length
  }), [appCounts, serverStats, apps])

  const applicationCategories = useMemo(() => {
    const map = new Map<string, { id: string; name: string; count: number }>()

    for (const app of apps) {
      const entry = map.get(app.category.id)
      if (entry) {
        entry.count += 1
      } else {
        map.set(app.category.id, {
          id: app.category.id,
          name: app.category.name,
          count: 1
        })
      }
    }

    return Array.from(map.values())
  }, [apps])

  // Navigation items with dynamic counts
  const navigationItems: NavItem[] = useMemo(() => [
    {
      id: 'dashboard',
      label: t('nav.dashboard'),
      href: '/',
      icon: Home,
      description: t('dashboard.overview', 'System overview and health')
    },
    {
      id: 'servers',
      label: t('nav.servers'),
      href: '/servers',
      icon: Server,
      description: t('servers.title', 'Manage your servers'),
      badge: stats.connectedServers > 0 && stats.connectedServers < stats.totalServers ? stats.connectedServers : undefined
    },
    {
      id: 'applications',
      label: t('nav.applications'),
      href: '/applications',
      icon: Package,
      description: t('applications.title', 'App marketplace and management'),
      subItems: [
        { label: t('applications.allApps', 'All Apps'), href: '/applications', count: appCounts.totalApps },
        ...applicationCategories.map(cat => ({
          label: cat.name,
          href: `/applications?category=${cat.id}`,
          count: cat.count
        }))
      ]
    },
    {
      id: 'logs',
      label: t('nav.logs'),
      href: '/logs',
      icon: FileText,
      description: t('logs.title', 'System and application logs'),
      parentOnly: true,
      alwaysExpanded: true,
      subItems: [
        { label: t('nav.accessLogs'), href: '/logs/access', icon: Shield },
        { label: t('nav.auditLogs'), href: '/logs/audit', icon: ScrollText }
      ]
    }
  ], [stats, appCounts, t, applicationCategories])

  // Active state detection
  const isActiveItem = (item: NavItem): boolean => {
    if (item.subItems) {
      // For items with sub-items, never mark as active
      // Only the sub-items themselves should be active
      return false
    }
    return location.pathname === item.href
  }

  const isActiveSubItem = (subItem: SubNavItem): boolean => {
    // Special handling for "All Apps" - only active when no query parameters
    if (subItem.href === '/applications') {
      return location.pathname === '/applications' && !location.search
    }
    
    // Handle items with query parameters
    if (subItem.href.includes('?')) {
      const [path, query] = subItem.href.split('?')
      return location.pathname === path && location.search === `?${query}`
    }
    
    return location.pathname === subItem.href
  }

  // Helper to determine if a parent item should be expanded (any sub-item is active)
  const shouldExpand = (item: NavItem): boolean => {
    if (!item.subItems) return false
    return item.subItems.some(subItem => isActiveSubItem(subItem))
  }

  return {
    navigationItems,
    stats,
    isActiveItem,
    isActiveSubItem,
    shouldExpand,
    currentPath: location.pathname
  }
}
