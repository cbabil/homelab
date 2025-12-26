/**
 * Dashboard Loading State Component
 * 
 * Loading skeleton shown while dashboard data is being fetched.
 */

export function DashboardLoadingState() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="h-8 bg-muted rounded w-48" />
        <div className="h-4 bg-muted rounded w-96" />
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-card p-6 rounded-xl border card-hover">
            <div className="space-y-3">
              <div className="w-12 h-12 bg-muted rounded-lg" />
              <div className="h-6 bg-muted rounded w-20" />
              <div className="h-4 bg-muted rounded w-32" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}