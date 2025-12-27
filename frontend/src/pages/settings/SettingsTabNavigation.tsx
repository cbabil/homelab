/**
 * Settings Tab Navigation Component
 *
 * Tab navigation for switching between different settings sections.
 */

import { Server, Monitor, Shield, Bell, ShoppingCart } from 'lucide-react'
import { cn } from '@/utils/cn'
import { Tab } from './types'
import { Button } from '@/components/ui/Button'

const tabs: Tab[] = [
  {
    id: 'general',
    label: 'General',
    icon: Monitor
  },
  {
    id: 'security',
    label: 'Security',
    icon: Shield
  },
  {
    id: 'notifications',
    label: 'Notifications',
    icon: Bell
  },
  {
    id: 'servers',
    label: 'Servers',
    icon: Server
  },
  {
    id: 'marketplace',
    label: 'Marketplace',
    icon: ShoppingCart
  }
]

interface SettingsTabNavigationProps {
  activeTab: string
  onTabChange: (tabId: string) => void
}

export function SettingsTabNavigation({ activeTab, onTabChange }: SettingsTabNavigationProps) {
  return (
    <div className="flex space-x-1 bg-muted p-1 rounded-lg w-fit flex-shrink-0">
      {tabs.map((tab) => {
        const Icon = tab.icon
        return (
          <Button
            key={tab.id}
            variant="ghost"
            size="sm"
            onClick={() => onTabChange(tab.id)}
            className={cn(
              activeTab === tab.id && 'bg-background shadow-sm text-primary'
            )}
            leftIcon={<Icon className="h-4 w-4" />}
          >
            {tab.label}
          </Button>
        )
      })}
    </div>
  )
}