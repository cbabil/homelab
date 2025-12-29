/**
 * Navigation Sidebar Component
 *
 * Uses ui-toolkit SideMenu for consistent navigation with
 * real-time stats and marketplace footer.
 */

import { useNavigate, useLocation } from 'react-router-dom'
import { ShoppingCart } from 'lucide-react'
import { SideMenu, type SideMenuItem } from 'ui-toolkit'
import { useNavigation } from '@/hooks/useNavigation'
import { QuickStats } from './QuickStats'

export function Navigation() {
  const navigate = useNavigate()
  const location = useLocation()
  const { stats, navigationItems: navData } = useNavigation()

  // Build SideMenu items from navigation data (no sub-items)
  const menuItems: SideMenuItem[] = navData.map((item) => ({
    label: item.label,
    value: item.href,
    icon: <item.icon size={16} />,
    badge: item.badge !== undefined ? (
      <span className="text-xs px-1.5 py-0.5 rounded-full bg-destructive text-destructive-foreground">
        {item.badge}
      </span>
    ) : undefined
  }))

  // Marketplace in footer
  const footerItems: SideMenuItem[] = [
    {
      label: 'Marketplace',
      value: '/marketplace',
      icon: <ShoppingCart size={16} />
    }
  ]

  const handleSelect = (value: string) => {
    navigate(value)
  }

  return (
    <aside className="w-64 border-r border-border bg-background flex flex-col h-full">
      {/* Main Navigation */}
      <SideMenu
        items={menuItems}
        active={location.pathname}
        onSelect={handleSelect}
        header="Navigation"
      />

      {/* Quick Stats */}
      <QuickStats stats={stats} />

      {/* Spacer + Marketplace */}
      <div className="flex-1" />
      <div className="px-4 pb-4">
        <SideMenu
          items={footerItems}
          active={location.pathname}
          onSelect={handleSelect}
        />
      </div>
    </aside>
  )
}
