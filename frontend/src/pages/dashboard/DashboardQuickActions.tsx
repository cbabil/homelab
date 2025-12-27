/**
 * Dashboard Quick Actions Component
 *
 * Quick action buttons for common dashboard operations.
 */

import { Server, Package, TrendingUp } from 'lucide-react'
import { Button } from '@/components/ui/Button'

export function DashboardQuickActions() {
  return (
    <div className="bg-card p-6 rounded-xl border card-hover">
      <div className="flex items-center space-x-3 mb-6">
        <div className="p-2 rounded-lg bg-primary/10">
          <TrendingUp className="w-5 h-5 text-primary" />
        </div>
        <h2 className="text-xl font-semibold">Quick Actions</h2>
      </div>

      <div className="space-y-3">
        <Button
          variant="ghost"
          className="w-full justify-start p-3"
          leftIcon={<Server className="w-4 h-4" />}
        >
          Manage Servers
        </Button>

        <Button
          variant="ghost"
          className="w-full justify-start p-3"
          leftIcon={<Package className="w-4 h-4" />}
        >
          Browse Applications
        </Button>
      </div>
    </div>
  )
}