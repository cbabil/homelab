/**
 * Server Stats Card Component
 * 
 * Reusable statistics card component for displaying server metrics.
 * Used in the statistics dashboard section.
 */

import { LucideIcon } from 'lucide-react'

interface ServerStatsCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  iconColor: string
  bgColor: string
}

export function ServerStatsCard({ 
  title, 
  value, 
  icon: Icon, 
  iconColor, 
  bgColor 
}: ServerStatsCardProps) {
  return (
    <div className="bg-card p-6 rounded-xl border shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center space-x-4">
        <div className={`p-3 rounded-xl ${bgColor}`}>
          <Icon className={`h-6 w-6 ${iconColor}`} />
        </div>
        <div>
          <p className="text-sm text-muted-foreground font-medium">{title}</p>
          <p className="text-3xl font-bold">{value}</p>
        </div>
      </div>
    </div>
  )
}