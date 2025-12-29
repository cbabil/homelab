/**
 * Dashboard Quick Actions Component
 *
 * Quick action buttons for common dashboard operations.
 */

import { useNavigate } from 'react-router-dom'
import { Server, Package, Settings, ShoppingCart, TrendingUp, ChevronRight } from 'lucide-react'
import { Card } from 'ui-toolkit'

interface QuickAction {
  label: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  path: string
  iconBg: string
  iconColor: string
}

const quickActions: QuickAction[] = [
  {
    label: 'Manage Servers',
    description: 'View and configure servers',
    icon: Server,
    path: '/servers',
    iconBg: 'bg-blue-100 dark:bg-blue-900/30',
    iconColor: 'text-blue-600'
  },
  {
    label: 'Browse Applications',
    description: 'Install and manage apps',
    icon: Package,
    path: '/applications',
    iconBg: 'bg-purple-100 dark:bg-purple-900/30',
    iconColor: 'text-purple-600'
  },
  {
    label: 'App Marketplace',
    description: 'Discover new applications',
    icon: ShoppingCart,
    path: '/marketplace',
    iconBg: 'bg-green-100 dark:bg-green-900/30',
    iconColor: 'text-green-600'
  },
  {
    label: 'Settings',
    description: 'Configure preferences',
    icon: Settings,
    path: '/settings',
    iconBg: 'bg-gray-100 dark:bg-gray-900/30',
    iconColor: 'text-gray-600'
  }
]

export function DashboardQuickActions() {
  const navigate = useNavigate()

  return (
    <Card padding="md" className="h-full">
      <div className="flex items-center gap-2 mb-6">
        <div className="p-2 rounded-lg bg-primary/10">
          <TrendingUp className="w-5 h-5 text-primary" />
        </div>
        <h2 className="text-lg font-semibold">Quick Actions</h2>
      </div>

      <div className="space-y-2">
        {quickActions.map((action) => {
          const Icon = action.icon
          return (
            <button
              key={action.path}
              onClick={() => navigate(action.path)}
              className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors text-left group"
            >
              <div className={`p-2 rounded-lg ${action.iconBg} flex-shrink-0`}>
                <Icon className={`w-4 h-4 ${action.iconColor}`} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{action.label}</p>
                <p className="text-xs text-muted-foreground">{action.description}</p>
              </div>
              <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
            </button>
          )
        })}
      </div>
    </Card>
  )
}
