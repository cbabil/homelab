/**
 * General Settings Component
 * 
 * Application-wide general preferences, configuration, and backup/restore functionality.
 */

import { SettingRow } from './components'
import { BackupSection } from '@/components/settings/BackupSection'
import { TimezoneDropdown } from '@/components/settings/TimezoneDropdown'
import { DataRetentionSettings } from './components/DataRetentionSettings'

export function GeneralSettings() {
  return (
    <div className="space-y-4">
      <div className="bg-card rounded-lg border p-3">
        <h4 className="text-sm font-semibold mb-3 text-primary">Application</h4>
        <div className="space-y-0">
          <SettingRow 
            label="Auto-refresh"
            children={
              <select className="px-2 py-1 border border-input rounded text-sm bg-background min-w-20">
                <option>30s</option>
                <option>1m</option>
                <option>5m</option>
              </select>
            }
          />
          <SettingRow
            label="Default page"
            children={
              <select className="px-2 py-1 border border-input rounded text-sm bg-background min-w-24">
                <option>Dashboard</option>
                <option>Servers</option>
              </select>
            }
          />
          <SettingRow
            label="Timezone"
            children={<TimezoneDropdown />}
          />
        </div>
      </div>

      {/* Data Retention Section */}
      <DataRetentionSettings />

      {/* Backup & Restore Section */}
      <BackupSection />
    </div>
  )
}