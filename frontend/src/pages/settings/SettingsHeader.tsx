/**
 * Settings Page Header Component
 * 
 * Header section with title and description for the Settings page.
 */

export function SettingsHeader() {
  return (
    <div className="flex items-center justify-between flex-shrink-0">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">Configure your homelab preferences and connections</p>
      </div>
    </div>
  )
}