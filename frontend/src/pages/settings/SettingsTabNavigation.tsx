/**
 * Settings Tab Navigation Component
 * 
 * Tab navigation for switching between different settings sections.
 */

import { Server, Monitor, Shield, Bell } from 'lucide-react'
import { cn } from '@/utils/cn'
import { Tab } from './types'

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
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={cn(
              'flex items-center space-x-2 px-4 py-2 rounded text-sm font-medium transition-colors',
              activeTab === tab.id ? 'bg-background shadow-sm text-primary' : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <Icon className="h-4 w-4" />
            <span>{tab.label}</span>
          </button>
        )
      })}
    </div>
  )
}