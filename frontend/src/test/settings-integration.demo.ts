/**
 * Settings Integration Demo
 *
 * Demonstrates the integration between frontend settings and backend database
 * via MCP tools with fallback to localStorage.
 */

import { settingsService } from '@/services/settingsService'
import { SettingsMcpClient } from '@/services/settingsMcpClient'
import { HomelabMCPClient } from '@/services/mcpClient'
import { DEFAULT_SETTINGS } from '@/types/settings'

// Mock MCP client for testing
class MockMCPClient {
  private connected = true

  isBackendConnected() {
    return this.connected
  }

  async callTool<T>(name: string, params: Record<string, unknown>) {
    console.log(`Demo: MCP tool called - ${name}`, params)

    // Simulate backend responses
    switch (name) {
      case 'get_settings':
        return {
          success: true,
          data: {
            ...DEFAULT_SETTINGS,
            ui: {
              ...DEFAULT_SETTINGS.ui,
              theme: 'light' // Different from default to show database value
            },
            lastUpdated: new Date().toISOString(),
            version: 2
          }
        }

      case 'update_settings':
        return {
          success: true,
          data: {
            ...params.settings,
            lastUpdated: new Date().toISOString(),
            version: (params.settings as any).version + 1
          }
        }

      case 'validate_settings':
        return {
          success: true,
          data: {
            isValid: true,
            errors: [],
            warnings: []
          }
        }

      default:
        return {
          success: false,
          error: `Unknown tool: ${name}`
        }
    }
  }

  setConnected(connected: boolean) {
    this.connected = connected
  }
}

/**
 * Demo function showing settings integration
 */
export async function demonstrateSettingsIntegration() {
  console.log('🚀 Settings Integration Demo Starting...')

  // Create mock MCP client
  const mockMcpClient = new MockMCPClient()
  const settingsMcpClient = new SettingsMcpClient(
    mockMcpClient as any,
    () => mockMcpClient.isBackendConnected()
  )

  try {
    console.log('1️⃣ Initializing settings service with MCP client...')
    const initialSettings = await settingsService.initialize(settingsMcpClient, 'demo-user')
    console.log('✅ Settings initialized:', {
      theme: initialSettings.ui.theme,
      version: initialSettings.version,
      isUsingDatabase: settingsService.isUsingDatabase()
    })

    console.log('2️⃣ Updating settings (should use database)...')
    const updateResult = await settingsService.updateSettings('ui', {
      theme: 'dark',
      compactMode: true
    })
    console.log('✅ Settings updated:', {
      success: updateResult.success,
      newTheme: updateResult.settings?.ui.theme,
      newVersion: updateResult.settings?.version
    })

    console.log('3️⃣ Simulating database disconnection...')
    mockMcpClient.setConnected(false)

    const updateResult2 = await settingsService.updateSettings('ui', {
      language: 'es'
    })
    console.log('✅ Settings updated (fallback mode):', {
      success: updateResult2.success,
      isUsingDatabase: settingsService.isUsingDatabase()
    })

    console.log('4️⃣ Reconnecting and syncing from database...')
    mockMcpClient.setConnected(true)
    const syncResult = await settingsService.syncFromDatabase()
    console.log('✅ Sync result:', {
      success: syncResult.success,
      isUsingDatabase: settingsService.isUsingDatabase()
    })

    console.log('🎉 Settings Integration Demo Complete!')
    return true

  } catch (error) {
    console.error('❌ Demo failed:', error)
    return false
  }
}

/**
 * Demo showing error handling and validation
 */
export async function demonstrateErrorHandling() {
  console.log('🔧 Error Handling Demo Starting...')

  try {
    // Test validation
    console.log('1️⃣ Testing validation...')
    const invalidSettings = {
      ...DEFAULT_SETTINGS,
      security: {
        ...DEFAULT_SETTINGS.security,
        session: {
          ...DEFAULT_SETTINGS.security.session,
          timeout: 'invalid' as any
        }
      }
    }

    const validation = await settingsService['validateSettings'](invalidSettings)
    console.log('✅ Validation result:', validation)

    // Test with disconnected backend
    console.log('2️⃣ Testing without MCP client...')
    const settingsWithoutMcp = await settingsService.initialize(null, 'test-user')
    console.log('✅ Fallback initialization:', {
      theme: settingsWithoutMcp.ui.theme,
      isUsingDatabase: settingsService.isUsingDatabase()
    })

    console.log('🎉 Error Handling Demo Complete!')
    return true

  } catch (error) {
    console.error('❌ Error handling demo failed:', error)
    return false
  }
}

// Export for console testing
if (typeof window !== 'undefined') {
  (window as any).settingsDemo = {
    demonstrateSettingsIntegration,
    demonstrateErrorHandling,
    settingsService
  }
}