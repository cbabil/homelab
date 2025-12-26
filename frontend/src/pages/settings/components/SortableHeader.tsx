/**
 * Sortable Header Component
 * 
 * Reusable sortable table header with visual indicators.
 */

import { ChevronUp, ChevronDown } from 'lucide-react'
import { cn } from '@/utils/cn'
import type { SortKey } from '../types'

interface SortableHeaderProps {
  label: string
  sortKey: SortKey
  currentSort: SortKey
  sortOrder: 'asc' | 'desc'
  onSort: (key: SortKey) => void
}

export function SortableHeader({ 
  label, 
  sortKey, 
  currentSort, 
  sortOrder, 
  onSort 
}: SortableHeaderProps) {
  const isActive = currentSort === sortKey
  
  return (
    <th 
      className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider cursor-pointer hover:text-foreground transition-colors select-none"
      onClick={() => onSort(sortKey)}
    >
      <div className="flex items-center space-x-1">
        <span>{label}</span>
        <div className="flex flex-col">
          <ChevronUp 
            className={cn(
              "h-3 w-3", 
              isActive && sortOrder === 'asc' 
                ? 'text-primary' 
                : 'text-muted-foreground/50'
            )}
          />
          <ChevronDown 
            className={cn(
              "h-3 w-3 -mt-1", 
              isActive && sortOrder === 'desc' 
                ? 'text-primary' 
                : 'text-muted-foreground/50'
            )}
          />
        </div>
      </div>
    </th>
  )
}