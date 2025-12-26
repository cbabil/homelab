/**
 * Info Item Component
 * 
 * Displays individual server information items with icon and label/value pairs.
 */

import { type ComponentType } from 'react'
import { cn } from '@/utils/cn'

interface InfoItemProps {
  icon: ComponentType<{ className?: string }>
  label: string
  value?: string
  className?: string
}

export function InfoItem({ icon: Icon, label, value, className }: InfoItemProps) {
  const getNotAvailableMessage = (label: string) => {
    if (label.includes('Docker')) return 'Docker not installed'
    if (label.includes('OS')) return 'OS information unavailable'
    if (label.includes('Architecture')) return 'Architecture unavailable'
    if (label.includes('Uptime')) return 'Uptime unavailable'
    if (label.includes('Kernel')) return 'Kernel info unavailable'
    return 'Not available'
  }
  
  return (
    <div className={cn("flex items-center space-x-2", className)}>
      <Icon className="h-3 w-3 text-muted-foreground flex-shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="text-xs text-muted-foreground truncate">{label}</p>
        <p className={cn("text-xs truncate", value ? "font-medium" : "font-normal text-muted-foreground italic")}>
          {value || getNotAvailableMessage(label)}
        </p>
      </div>
    </div>
  )
}