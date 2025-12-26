/**
 * Category Grid Component
 * 
 * Grid of application categories for filtering.
 */

import { Home } from 'lucide-react'
import { AppCategory } from '@/types/app'
import { cn } from '@/utils/cn'

interface CategoryGridProps {
  categories: AppCategory[]
  selectedCategory: string | null
  onCategorySelect: (categoryId: string | null) => void
  appCounts: Record<string, number>
  totalApps: number
}

export function CategoryGrid({ 
  categories, 
  selectedCategory, 
  onCategorySelect, 
  appCounts, 
  totalApps 
}: CategoryGridProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <button
        onClick={() => onCategorySelect(null)}
        className={cn(
          "p-4 rounded-xl border text-left h-full",
          selectedCategory === null 
            ? "border-primary bg-primary/5" 
            : "border-border"
        )}
      >
        <div className="space-y-2">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10">
            <Home className="h-5 w-5 text-primary" />
          </div>
          <div className="space-y-1">
            <p className="font-medium text-sm">All Apps</p>
            <p className="text-xs text-muted-foreground">{totalApps} available</p>
          </div>
        </div>
      </button>

      {categories.map((category) => {
        const IconComponent = category.icon
        return (
          <button
            key={category.id}
            onClick={() => onCategorySelect(category.id)}
            className={cn(
              "p-4 rounded-xl border text-left h-full",
              selectedCategory === category.id 
                ? "border-primary bg-primary/5" 
                : "border-border"
            )}
          >
            <div className="space-y-2">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10">
                <IconComponent className="h-5 w-5 text-primary" />
              </div>
              <div className="space-y-1">
                <p className="font-medium text-sm">{category.name}</p>
                <p className="text-xs text-muted-foreground">
                  {appCounts[category.id] || 0} apps
                </p>
              </div>
            </div>
          </button>
        )
      })}
    </div>
  )
}