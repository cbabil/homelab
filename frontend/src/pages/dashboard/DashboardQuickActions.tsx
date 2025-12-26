/**
 * Dashboard Quick Actions Component
 * 
 * Quick action buttons for common dashboard operations.
 */

import { Server, Package, TrendingUp } from 'lucide-react'

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
        <button className="w-full text-left p-3 rounded-lg hover:bg-accent transition-colors duration-200 group">
          <div className="flex items-center space-x-3">
            <Server className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
            <span className="font-medium group-hover:text-foreground transition-colors">
              Manage Servers
            </span>
          </div>
        </button>
        
        <button className="w-full text-left p-3 rounded-lg hover:bg-accent transition-colors duration-200 group">
          <div className="flex items-center space-x-3">
            <Package className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
            <span className="font-medium group-hover:text-foreground transition-colors">
              Browse Applications
            </span>
          </div>
        </button>
      </div>
    </div>
  )
}