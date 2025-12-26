/**
 * Navigation Sidebar Component
 * 
 * Enhanced modular sidebar with real-time stats, improved UX,
 * and component-based architecture for better maintainability.
 */

import { useState } from 'react'
import { useNavigation, type NavItem } from '@/hooks/useNavigation'
import { NavigationSection } from './NavigationSection'
import { NavigationItem } from './NavigationItem'
import { QuickStats } from './QuickStats'
import packageJson from '../../../package.json'


export function Navigation() {
  const { navigationItems, stats, isActiveItem, isActiveSubItem, shouldExpand } = useNavigation()
  const [expandedItems, setExpandedItems] = useState<string[]>(['applications'])
  
  const handleToggleExpanded = (itemId: string) => {
    setExpandedItems(prev => 
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    )
  }
  
  const handleSubItemClick = () => {
    // Could add analytics or other side effects here
  }

  // Auto-expand items when their sub-items are active
  const isExpanded = (item: NavItem): boolean => {
    return expandedItems.includes(item.id) || shouldExpand(item)
  }

  return (
    <aside className="w-64 border-r border-border bg-background flex flex-col h-full">
      {/* Main Navigation */}
      <nav className="flex-1 overflow-y-auto scrollbar-thin scrollbar-track-transparent scrollbar-thumb-border/20 hover:scrollbar-thumb-border/40">
        <NavigationSection title="Navigation" className="px-3 pt-4 pb-2">
          <div className="space-y-0.5">
            {navigationItems.map((item) => (
              <NavigationItem
                key={item.id}
                item={item}
                isActive={isActiveItem(item)}
                isExpanded={isExpanded(item)}
                onToggle={() => handleToggleExpanded(item.id)}
                onSubItemClick={handleSubItemClick}
                isActiveSubItem={isActiveSubItem}
              />
            ))}
          </div>
        </NavigationSection>
        
        {/* Quick Stats Section */}
        <NavigationSection showDivider className="pb-4">
          <QuickStats stats={stats} />
        </NavigationSection>
      </nav>
      
      {/* Footer */}
      <footer className="px-4 py-3 border-t border-border/50 bg-muted/20">
        <div className="text-xs text-muted-foreground text-center">
          <div className="font-medium">Homelab Assistant</div>
          <div className="opacity-60 mt-0.5">v{packageJson.version}</div>
        </div>
      </footer>
    </aside>
  )
}
