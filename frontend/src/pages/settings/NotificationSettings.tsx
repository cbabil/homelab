/**
 * Notification Settings Component
 * 
 * System alerts and notification preferences configuration.
 */

import { Toggle, SettingRow } from './components'

interface NotificationSettingsProps {
  serverAlerts: boolean
  resourceAlerts: boolean
  updateAlerts: boolean
  onServerAlertsChange: (checked: boolean) => void
  onResourceAlertsChange: (checked: boolean) => void
  onUpdateAlertsChange: (checked: boolean) => void
}

export function NotificationSettings({
  serverAlerts,
  resourceAlerts,
  updateAlerts,
  onServerAlertsChange,
  onResourceAlertsChange,
  onUpdateAlertsChange
}: NotificationSettingsProps) {
  return (
    <div className="space-y-4">
      <div className="bg-card rounded-lg border p-3">
        <h4 className="text-sm font-semibold mb-3 text-primary">System Alerts</h4>
        <div className="space-y-0">
          <SettingRow 
            label="Server alerts" 
            children={
              <Toggle checked={serverAlerts} onChange={onServerAlertsChange} />
            } 
          />
          <SettingRow 
            label="Resource alerts" 
            children={
              <Toggle checked={resourceAlerts} onChange={onResourceAlertsChange} />
            } 
          />
          <SettingRow 
            label="Update alerts" 
            children={
              <Toggle checked={updateAlerts} onChange={onUpdateAlertsChange} />
            } 
          />
        </div>
      </div>
    </div>
  )
}