/**
 * Shared Settings Components
 * 
 * Common UI components used across settings tabs.
 */

import React from 'react'
import { cn } from '@/utils/cn'

// Re-export specialized components
export { SortableHeader } from './components/SortableHeader'
export { SessionTable } from './components/SessionTable'
export { SessionTableHeader } from './components/SessionTableHeader'
export { SessionRow } from './components/SessionRow'

interface ToggleProps {
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
}

export function Toggle({ checked, onChange, disabled = false }: ToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => !disabled && onChange(!checked)}
      className={cn(
        'relative inline-flex h-4 w-8 shrink-0 rounded-full border-2 border-transparent',
        'focus:outline-none',
        disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer',
        checked ? 'bg-primary' : 'bg-gray-200 dark:bg-gray-700'
      )}
    >
      <span className={cn(
        'pointer-events-none inline-block h-3 w-3 transform rounded-full bg-white shadow ring-0',
        'transition-transform duration-200 ease-in-out',
        checked ? 'translate-x-4' : 'translate-x-0'
      )} />
    </button>
  )
}

interface SettingRowProps {
  label: string
  children: React.ReactNode
}

export function SettingRow({ label, children }: SettingRowProps) {
  return (
    <div className="flex items-center justify-between py-2 gap-4">
      <span className="text-sm font-medium flex-shrink-0">{label}</span>
      <div className="flex-1 flex justify-end min-w-0">
        {children}
      </div>
    </div>
  )
}