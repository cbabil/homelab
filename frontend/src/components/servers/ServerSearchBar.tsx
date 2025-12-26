/**
 * Server Search Bar Component
 * 
 * Enhanced search input with modern styling and result counter.
 * Positioned prominently at the top of server cards section.
 */

import { Search } from 'lucide-react'

interface ServerSearchBarProps {
  searchTerm: string
  onSearchChange: (term: string) => void
  resultCount: number
  totalCount: number
}

export function ServerSearchBar({ 
  searchTerm, 
  onSearchChange, 
  resultCount, 
  totalCount 
}: ServerSearchBarProps) {
  return (
    <div className="flex items-center justify-between gap-6 p-6 bg-card/30 border border-border/60 rounded-xl backdrop-blur-sm">
      <div className="relative flex-1 max-w-2xl">
        <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-muted-foreground h-5 w-5" />
        <input
          type="text"
          placeholder="Search servers by name, host, or username..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full pl-12 pr-4 py-3.5 text-lg border-2 border-input/60 rounded-xl bg-background/80 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-200 shadow-sm hover:shadow-md placeholder:text-muted-foreground/70"
        />
      </div>
      {resultCount > 0 && (
        <div className="text-sm font-medium text-muted-foreground bg-muted/50 px-4 py-2 rounded-lg border">
          <span className="text-foreground font-semibold">{resultCount}</span> of {totalCount} servers
        </div>
      )}
    </div>
  )
}