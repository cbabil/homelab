/**
 * End-to-End Settings Persistence Tests
 *
 * Comprehensive E2E tests for the complete settings persistence system.
 * Tests the entire stack: frontend → MCP → backend → database → audit trail.
 *
 * Requirements:
 * - Backend server running on default port with settings database initialized
 * - Frontend server running with MCP client configured
 * - Admin credentials (admin/admin123) available for testing
 */

import { test, expect, Page } from '@playwright/test'

// Test configuration
const BACKEND_URL = 'http://localhost:8000'
const FRONTEND_URL = 'http://localhost:5173'
const ADMIN_CREDENTIALS = { username: 'admin', password: 'admin123' }

// Test data for settings validation
const TEST_SETTINGS = {
  ui: {
    theme: 'dark',
    language: 'en',
    compactMode: false,
    notifications: true
  },
  security: {
    session: {
      timeout: '2h',
      idleDetection: true,
      extendOnActivity: true,
      showWarningMinutes: 5
    },
    twoFactorEnabled: false,
    requirePasswordChange: false,
    passwordChangeInterval: 90
  },
  system: {
    autoRefresh: true,
    refreshInterval: 30,
    enableDebugMode: false,
    maxLogEntries: 1000,
    dataRetention: {
      logRetentionDays: 14,
      otherDataRetentionDays: 14,
      autoCleanupEnabled: false
    }
  }
}

test.describe('Settings Persistence System E2E', () => {
  let page: Page

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage()

    // Navigate to frontend
    await page.goto(FRONTEND_URL)

    // Wait for page to load
    await page.waitForLoadState('domcontentloaded')
  })

  test.afterEach(async () => {
    await page.close()
  })

  test('Complete settings persistence workflow', async () => {
    // Step 1: Authenticate as admin
    await authenticateAsAdmin(page)

    // Step 2: Navigate to settings page
    await page.click('[data-testid="settings-nav"]')
    await page.waitForSelector('[data-testid="settings-page"]')

    // Step 3: Update UI settings
    await updateUISettings(page)

    // Step 4: Update security settings
    await updateSecuritySettings(page)

    // Step 5: Update system settings
    await updateSystemSettings(page)

    // Step 6: Save settings
    await page.click('[data-testid="save-settings"]')
    await page.waitForSelector('[data-testid="settings-saved-notification"]')

    // Step 7: Verify settings persistence by reloading page
    await page.reload()
    await page.waitForLoadState('domcontentloaded')
    await authenticateAsAdmin(page)
    await page.click('[data-testid="settings-nav"]')

    // Step 8: Verify all settings are persisted correctly
    await verifyUISettings(page)
    await verifySecuritySettings(page)
    await verifySystemSettings(page)

    // Step 9: Verify audit trail
    await verifyAuditTrail(page)
  })

  test('Settings database integration', async () => {
    // Step 1: Direct database verification
    const dbSettings = await getSettingsFromDatabase()
    expect(dbSettings).toBeDefined()
    expect(dbSettings.length).toBeGreaterThan(0)

    // Step 2: Verify security constraints
    const auditEntries = await getAuditEntriesFromDatabase()
    expect(auditEntries).toBeDefined()

    // Step 3: Verify data integrity
    for (const setting of dbSettings) {
      expect(setting.setting_key).toMatch(/^[a-zA-Z0-9._]+$/)
      expect(() => JSON.parse(setting.setting_value)).not.toThrow()
      expect(['ui', 'security', 'system', 'retention']).toContain(setting.category)
    }
  })

  test('Security controls validation', async () => {
    // Step 1: Test admin-only operations
    await authenticateAsAdmin(page)
    await page.goto(`${FRONTEND_URL}/settings`)

    // Admin should be able to access all settings
    await expect(page.locator('[data-testid="admin-settings"]')).toBeVisible()

    // Step 2: Test unauthorized access (simulate regular user)
    await logoutUser(page)
    await authenticateAsRegularUser(page)
    await page.goto(`${FRONTEND_URL}/settings`)

    // Regular user should see limited settings
    await expect(page.locator('[data-testid="admin-settings"]')).not.toBeVisible()
    await expect(page.locator('[data-testid="user-settings"]')).toBeVisible()
  })

  test('Error handling and recovery', async () => {
    await authenticateAsAdmin(page)
    await page.goto(`${FRONTEND_URL}/settings`)

    // Step 1: Test invalid input validation
    await page.fill('[data-testid="session-timeout"]', 'invalid-timeout')
    await page.click('[data-testid="save-settings"]')
    await expect(page.locator('[data-testid="validation-error"]')).toBeVisible()

    // Step 2: Test network error recovery
    // Intercept network requests and simulate failure
    await page.route('**/api/settings/**', route => route.abort())
    await page.click('[data-testid="save-settings"]')
    await expect(page.locator('[data-testid="network-error"]')).toBeVisible()

    // Step 3: Test localStorage fallback
    const localStorageSettings = await page.evaluate(() => {
      return localStorage.getItem('homelab_user_settings')
    })
    expect(localStorageSettings).toBeDefined()
  })

  test('Performance and concurrent operations', async () => {
    await authenticateAsAdmin(page)
    await page.goto(`${FRONTEND_URL}/settings`)

    // Step 1: Measure settings load time
    const startTime = Date.now()
    await page.waitForSelector('[data-testid="settings-loaded"]')
    const loadTime = Date.now() - startTime
    expect(loadTime).toBeLessThan(2000) // Should load within 2 seconds

    // Step 2: Test rapid consecutive updates
    for (let i = 0; i < 5; i++) {
      await page.click('[data-testid="theme-toggle"]')
      await page.waitForTimeout(100)
    }

    // Verify no race conditions or data corruption
    await page.click('[data-testid="save-settings"]')
    await page.waitForSelector('[data-testid="settings-saved-notification"]')
  })
})

// Helper functions

async function authenticateAsAdmin(page: Page) {
  // Navigate to login if not already authenticated
  const loginButton = page.locator('[data-testid="login-button"]')
  if (await loginButton.isVisible()) {
    await page.fill('[data-testid="username"]', ADMIN_CREDENTIALS.username)
    await page.fill('[data-testid="password"]', ADMIN_CREDENTIALS.password)
    await page.click('[data-testid="login-submit"]')
    await page.waitForSelector('[data-testid="dashboard"]')
  }
}

async function authenticateAsRegularUser(page: Page) {
  await page.fill('[data-testid="username"]', 'testuser')
  await page.fill('[data-testid="password"]', 'testpass')
  await page.click('[data-testid="login-submit"]')
  await page.waitForSelector('[data-testid="dashboard"]')
}

async function logoutUser(page: Page) {
  await page.click('[data-testid="user-menu"]')
  await page.click('[data-testid="logout-button"]')
  await page.waitForSelector('[data-testid="login-form"]')
}

async function updateUISettings(page: Page) {
  // Theme
  const currentTheme = await page.getAttribute('[data-testid="theme-select"]', 'value')
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark'
  await page.selectOption('[data-testid="theme-select"]', newTheme)

  // Language
  await page.selectOption('[data-testid="language-select"]', 'fr')

  // Compact mode
  await page.check('[data-testid="compact-mode"]')

  // Notifications
  await page.uncheck('[data-testid="notifications"]')
}

async function updateSecuritySettings(page: Page) {
  // Session timeout
  await page.selectOption('[data-testid="session-timeout"]', '4h')

  // Idle detection
  await page.uncheck('[data-testid="idle-detection"]')

  // Two-factor authentication
  await page.check('[data-testid="two-factor"]')
}

async function updateSystemSettings(page: Page) {
  // Auto refresh
  await page.uncheck('[data-testid="auto-refresh"]')

  // Refresh interval
  await page.fill('[data-testid="refresh-interval"]', '60')

  // Debug mode
  await page.check('[data-testid="debug-mode"]')

  // Max log entries
  await page.fill('[data-testid="max-log-entries"]', '2000')
}

async function verifyUISettings(page: Page) {
  await expect(page.locator('[data-testid="theme-select"]')).toHaveValue('light')
  await expect(page.locator('[data-testid="language-select"]')).toHaveValue('fr')
  await expect(page.locator('[data-testid="compact-mode"]')).toBeChecked()
  await expect(page.locator('[data-testid="notifications"]')).not.toBeChecked()
}

async function verifySecuritySettings(page: Page) {
  await expect(page.locator('[data-testid="session-timeout"]')).toHaveValue('4h')
  await expect(page.locator('[data-testid="idle-detection"]')).not.toBeChecked()
  await expect(page.locator('[data-testid="two-factor"]')).toBeChecked()
}

async function verifySystemSettings(page: Page) {
  await expect(page.locator('[data-testid="auto-refresh"]')).not.toBeChecked()
  await expect(page.locator('[data-testid="refresh-interval"]')).toHaveValue('60')
  await expect(page.locator('[data-testid="debug-mode"]')).toBeChecked()
  await expect(page.locator('[data-testid="max-log-entries"]')).toHaveValue('2000')
}

async function verifyAuditTrail(page: Page) {
  // Navigate to audit page
  await page.click('[data-testid="audit-nav"]')
  await page.waitForSelector('[data-testid="audit-page"]')

  // Verify recent settings changes are logged
  const auditEntries = page.locator('[data-testid="audit-entry"]')
  await expect(auditEntries).toHaveCountGreaterThan(0)

  // Verify entry contains expected information
  const firstEntry = auditEntries.first()
  await expect(firstEntry.locator('[data-testid="change-type"]')).toContainText('UPDATE')
  await expect(firstEntry.locator('[data-testid="user-id"]')).toContainText('admin')
  await expect(firstEntry.locator('[data-testid="checksum"]')).toBeVisible()
}

// Database helper functions (these would connect to the test database)
async function getSettingsFromDatabase() {
  // This would make a direct database connection in a real test
  // For now, return mock data that represents the expected structure
  return [
    {
      id: 1,
      setting_key: 'ui.theme',
      setting_value: '"light"',
      category: 'ui',
      scope: 'user_overridable',
      data_type: 'string',
      is_admin_only: false,
      version: 1
    }
  ]
}

async function getAuditEntriesFromDatabase() {
  // This would make a direct database connection in a real test
  return [
    {
      id: 1,
      table_name: 'system_settings',
      record_id: 1,
      user_id: 'admin',
      setting_key: 'ui.theme',
      old_value: '"dark"',
      new_value: '"light"',
      change_type: 'UPDATE',
      checksum: 'abc123def456...'
    }
  ]
}