/**
 * Server Info Display Component
 * 
 * Compact server system information display with loading states.
 * Optimized for minimal vertical space usage.
 */

import { Cpu, Clock, Container, Monitor } from 'lucide-react'
import { SystemInfo, ServerStatus } from '@/types/server'
import { cn } from '@/utils/cn'
import { InfoItem } from './InfoItem'
import { LoadingState, ErrorState } from './ServerInfoStates'
import { formatUptime } from './ServerInfoUtils'

interface ServerInfoDisplayProps {
  systemInfo?: SystemInfo
  status: ServerStatus
  className?: string
}

export function ServerInfoDisplay({ systemInfo, status, className }: ServerInfoDisplayProps) {
  // Show loading state when preparing
  if (status === 'preparing') {
    return (
      <div className={cn("rounded-lg border bg-card/50", className)}>
        <LoadingState />
      </div>
    )
  }
  
  // Show error state when no system info is available and status indicates a problem
  if (!systemInfo && (status === 'error' || status === 'disconnected')) {
    return (
      <div className={cn("rounded-lg border bg-card/50", className)}>
        <ErrorState />
      </div>
    )
  }
  
  // Don't render anything if no system info and status is not problematic
  if (!systemInfo) {
    return null
  }

  return (
    <div className={cn("rounded-lg border bg-card/50 p-3 space-y-2", className)}>
      <div className="grid grid-cols-2 gap-2">
        <InfoItem 
          icon={Monitor} 
          label="OS" 
          value={systemInfo.os}
        />
        
        <InfoItem 
          icon={Cpu} 
          label="Arch" 
          value={systemInfo.architecture}
        />
        
        <InfoItem 
          icon={Clock} 
          label="Uptime" 
          value={formatUptime(systemInfo.uptime)}
        />
        
        <InfoItem 
          icon={Container} 
          label="Docker" 
          value={systemInfo.docker_version}
        />
      </div>
    </div>
  )
}