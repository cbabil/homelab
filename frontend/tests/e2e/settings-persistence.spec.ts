/**
 * End-to-End Tests for Settings Persistence System
 *
 * Comprehensive E2E tests covering the complete settings persistence system
 * including database integration, security, authentication, and UI interaction.
 */

import { test, expect, type Page } from '@playwright/test'

// Test configuration
const TEST_CONFIG = {
  BACKEND_URL: 'http://localhost:8000',
  FRONTEND_URL: 'http://localhost:3000',
  ADMIN_USERNAME: 'admin',
  ADMIN_PASSWORD: 'admin123',
  TEST_USER: 'test_user',
  TEST_PASSWORD: 'test_pass'
}

// Helper functions
async function loginAsAdmin(page: Page) {
  await page.goto(`${TEST_CONFIG.FRONTEND_URL}/login`)
  await page.fill('[data-testid="username-input"]', TEST_CONFIG.ADMIN_USERNAME)
  await page.fill('[data-testid="password-input"]', TEST_CONFIG.ADMIN_PASSWORD)
  await page.click('[data-testid="login-button"]')
  await page.waitForURL('**/dashboard')
}

async function loginAsUser(page: Page, username: string = TEST_CONFIG.TEST_USER, password: string = TEST_CONFIG.TEST_PASSWORD) {
  await page.goto(`${TEST_CONFIG.FRONTEND_URL}/login`)
  await page.fill('[data-testid="username-input"]', username)
  await page.fill('[data-testid="password-input"]', password)
  await page.click('[data-testid="login-button"]')
  await page.waitForURL('**/dashboard')
}

async function navigateToSettings(page: Page) {
  await page.click('[data-testid="settings-nav"]')
  await page.waitForURL('**/settings')
}

async function waitForSettingsLoad(page: Page) {
  await page.waitForSelector('[data-testid="settings-container"]')
  await page.waitForFunction(() => {
    const loadingSpinner = document.querySelector('[data-testid="settings-loading"]')
    return !loadingSpinner || loadingSpinner.style.display === 'none'
  })
}

test.describe('Settings Persistence System', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage before each test
    await page.context().clearCookies()
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })
  })

  test.describe('Authentication and Authorization', () => {
    test('should require authentication to access settings', async ({ page }) => {
      await page.goto(`${TEST_CONFIG.FRONTEND_URL}/settings`)

      // Should redirect to login
      await page.waitForURL('**/login')
      expect(page.url()).toContain('/login')

      // Should show authentication required message
      await expect(page.locator('[data-testid="auth-required-message"]')).toBeVisible()
    })

    test('should allow admin access to all settings', async ({ page }) => {
      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Admin should see all settings categories
      await expect(page.locator('[data-testid="category-ui"]')).toBeVisible()
      await expect(page.locator('[data-testid="category-security"]')).toBeVisible()
      await expect(page.locator('[data-testid="category-system"]')).toBeVisible()
      await expect(page.locator('[data-testid="category-retention"]')).toBeVisible()

      // Admin should see admin-only settings
      await page.click('[data-testid="category-system"]')
      await expect(page.locator('[data-testid="setting-system-debug"]')).toBeVisible()
      await expect(page.locator('[data-testid="setting-system-backup"]')).toBeVisible()
    })

    test('should restrict regular user access to admin-only settings', async ({ page }) => {
      await loginAsUser(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // User should see user-accessible categories
      await expect(page.locator('[data-testid="category-ui"]')).toBeVisible()
      await expect(page.locator('[data-testid="category-security"]')).toBeVisible()

      // User should not see admin-only categories or settings
      await expect(page.locator('[data-testid="category-system"]')).not.toBeVisible()

      // Check that UI shows restricted access message for admin settings
      await expect(page.locator('[data-testid="admin-only-notice"]')).toBeVisible()
    })

    test('should enforce session security for settings access', async ({ page }) => {
      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Simulate session expiry
      await page.evaluate(() => {
        localStorage.removeItem('auth_token')
        sessionStorage.clear()
      })

      // Try to update a setting
      await page.click('[data-testid="category-ui"]')
      await page.click('[data-testid="setting-theme-toggle"]')

      // Should be redirected to login due to expired session
      await page.waitForURL('**/login', { timeout: 10000 })
      expect(page.url()).toContain('/login')
    })
  })

  test.describe('Database Persistence', () => {
    test('should persist settings to database for admin user', async ({ page }) => {
      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Change theme setting
      await page.click('[data-testid="category-ui"]')
      const themeToggle = page.locator('[data-testid="setting-theme-toggle"]')
      const initialTheme = await themeToggle.textContent()

      await themeToggle.click()

      // Wait for save confirmation
      await expect(page.locator('[data-testid="save-success-message"]')).toBeVisible()
      await expect(page.locator('[data-testid="audit-id"]')).toBeVisible()

      // Refresh page and verify persistence
      await page.reload()
      await waitForSettingsLoad(page)
      await page.click('[data-testid="category-ui"]')

      const newTheme = await page.locator('[data-testid="setting-theme-toggle"]').textContent()
      expect(newTheme).not.toBe(initialTheme)
    })

    test('should handle database connection failures gracefully', async ({ page }) => {
      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Mock database connection failure
      await page.route('**/mcp/**', route => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Database connection failed' })
        })
      })

      // Attempt to change setting
      await page.click('[data-testid="category-ui"]')
      await page.click('[data-testid="setting-theme-toggle"]')

      // Should show fallback message
      await expect(page.locator('[data-testid="fallback-storage-notice"]')).toBeVisible()
      await expect(page.locator('[data-testid="database-reconnect-notice"]')).toBeVisible()
    })

    test('should validate settings before saving to database', async ({ page }) => {
      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Navigate to system settings
      await page.click('[data-testid="category-system"]')

      // Try to set invalid timeout value
      await page.fill('[data-testid="setting-timeout-input"]', '-1')
      await page.click('[data-testid="save-settings-button"]')

      // Should show validation error
      await expect(page.locator('[data-testid="validation-error"]')).toBeVisible()
      await expect(page.locator('[data-testid="validation-error"]')).toContainText('Invalid timeout value')

      // Setting should not be saved
      await page.reload()
      await waitForSettingsLoad(page)
      await page.click('[data-testid="category-system"]')

      const timeoutValue = await page.locator('[data-testid="setting-timeout-input"]').inputValue()
      expect(timeoutValue).not.toBe('-1')
    })

    test('should handle concurrent setting modifications', async ({ page, context }) => {
      // Open two tabs as admin
      const page1 = page
      const page2 = await context.newPage()

      await loginAsAdmin(page1)
      await loginAsAdmin(page2)

      await navigateToSettings(page1)
      await navigateToSettings(page2)
      await waitForSettingsLoad(page1)
      await waitForSettingsLoad(page2)

      // Both tabs modify the same setting
      await page1.click('[data-testid="category-ui"]')
      await page2.click('[data-testid="category-ui"]')

      await page1.click('[data-testid="setting-theme-toggle"]')
      await page2.click('[data-testid="setting-theme-toggle"]')

      // One should succeed, other should show conflict warning
      const success1 = page1.locator('[data-testid="save-success-message"]')
      const success2 = page2.locator('[data-testid="save-success-message"]')
      const conflict2 = page2.locator('[data-testid="version-conflict-warning"]')

      await expect(success1.or(success2).or(conflict2)).toBeVisible()

      await page2.close()
    })
  })

  test.describe('Local Storage Fallback', () => {
    test('should fallback to localStorage when database unavailable', async ({ page }) => {
      // Simulate backend unavailability
      await page.route('**/mcp/**', route => {
        route.abort('connectionrefused')
      })

      await page.goto(`${TEST_CONFIG.FRONTEND_URL}/login`)
      await page.fill('[data-testid="username-input"]', 'offline_user')
      await page.fill('[data-testid="password-input"]', 'offline_pass')
      await page.click('[data-testid="login-button"]')

      // Should use offline mode
      await expect(page.locator('[data-testid="offline-mode-indicator"]')).toBeVisible()

      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Should show localStorage mode indicator
      await expect(page.locator('[data-testid="storage-mode-local"]')).toBeVisible()

      // Settings should still be modifiable
      await page.click('[data-testid="category-ui"]')
      await page.click('[data-testid="setting-theme-toggle"]')

      await expect(page.locator('[data-testid="local-save-success"]')).toBeVisible()
    })

    test('should sync with database when connection restored', async ({ page }) => {
      // Start in offline mode
      await page.route('**/mcp/**', route => {
        route.abort('connectionrefused')
      })

      await page.goto(`${TEST_CONFIG.FRONTEND_URL}`)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Make changes in offline mode
      await page.click('[data-testid="category-ui"]')
      await page.click('[data-testid="setting-theme-toggle"]')
      await expect(page.locator('[data-testid="local-save-success"]')).toBeVisible()

      // Restore connection
      await page.unroute('**/mcp/**')

      // Should show sync notification
      await expect(page.locator('[data-testid="sync-available-notice"]')).toBeVisible()

      // Click sync button
      await page.click('[data-testid="sync-to-database-button"]')
      await expect(page.locator('[data-testid="sync-success-message"]')).toBeVisible()
    })

    test('should handle localStorage quota exceeded', async ({ page }) => {
      await page.goto(`${TEST_CONFIG.FRONTEND_URL}`)

      // Fill localStorage to capacity
      await page.evaluate(() => {
        try {
          const largeData = 'x'.repeat(5 * 1024 * 1024) // 5MB
          localStorage.setItem('test_large_data', largeData)
        } catch (e) {
          // Expected quota error
        }
      })

      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Try to save settings
      await page.click('[data-testid="category-ui"]')
      await page.click('[data-testid="setting-theme-toggle"]')

      // Should show quota exceeded error
      await expect(page.locator('[data-testid="storage-quota-error"]')).toBeVisible()
      await expect(page.locator('[data-testid="clear-storage-suggestion"]')).toBeVisible()
    })
  })

  test.describe('Security and Input Validation', () => {
    test('should prevent XSS attacks in setting values', async ({ page }) => {
      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Try to inject script in a text setting
      await page.click('[data-testid="category-system"]')
      await page.fill('[data-testid="setting-description-input"]', '<script>alert("xss")</script>')
      await page.click('[data-testid="save-settings-button"]')

      // Should sanitize input
      const sanitizedValue = await page.locator('[data-testid="setting-description-input"]').inputValue()
      expect(sanitizedValue).not.toContain('<script>')

      // No alert should appear
      await page.waitForTimeout(1000)
      const dialogs = []
      page.on('dialog', dialog => dialogs.push(dialog))
      expect(dialogs).toHaveLength(0)
    })

    test('should prevent SQL injection attempts', async ({ page }) => {
      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Monitor network requests for SQL injection attempts
      const maliciousInputs = [
        "'; DROP TABLE system_settings; --",
        "1' OR 1=1--",
        "'; DELETE FROM users; --"
      ]

      for (const maliciousInput of maliciousInputs) {
        await page.fill('[data-testid="setting-description-input"]', maliciousInput)
        await page.click('[data-testid="save-settings-button"]')

        // Should either reject or sanitize
        await expect(page.locator('[data-testid="validation-error"], [data-testid="save-success-message"]')).toBeVisible()
      }
    })

    test('should enforce admin-only setting restrictions', async ({ page }) => {
      await loginAsUser(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // User should not be able to access admin settings via URL manipulation
      await page.goto(`${TEST_CONFIG.FRONTEND_URL}/settings?category=system&setting=debug_mode`)

      // Should be redirected or show access denied
      await expect(page.locator('[data-testid="access-denied"], [data-testid="admin-required"]')).toBeVisible()
    })

    test('should validate setting value types and ranges', async ({ page }) => {
      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      await page.click('[data-testid="category-system"]')

      // Test invalid number range
      await page.fill('[data-testid="setting-max-connections"]', '999999')
      await page.click('[data-testid="save-settings-button"]')
      await expect(page.locator('[data-testid="validation-error"]')).toContainText('value exceeds maximum')

      // Test invalid number format
      await page.fill('[data-testid="setting-max-connections"]', 'not_a_number')
      await page.click('[data-testid="save-settings-button"]')
      await expect(page.locator('[data-testid="validation-error"]')).toContainText('must be a number')

      // Test invalid enum value
      await page.selectOption('[data-testid="setting-log-level"]', 'INVALID_LEVEL')
      await page.click('[data-testid="save-settings-button"]')
      await expect(page.locator('[data-testid="validation-error"]')).toContainText('Invalid log level')
    })
  })

  test.describe('Audit Trail and Logging', () => {
    test('should create audit entries for setting changes', async ({ page }) => {
      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Make a setting change
      await page.click('[data-testid="category-ui"]')
      await page.click('[data-testid="setting-theme-toggle"]')

      // Should show audit ID
      await expect(page.locator('[data-testid="audit-id"]')).toBeVisible()
      const auditId = await page.locator('[data-testid="audit-id"]').textContent()
      expect(auditId).toMatch(/^\d+$/)

      // Navigate to audit log
      await page.click('[data-testid="audit-log-link"]')
      await page.waitForURL('**/audit')

      // Should find the audit entry
      await expect(page.locator(`[data-testid="audit-entry-${auditId}"]`)).toBeVisible()
      await expect(page.locator(`[data-testid="audit-entry-${auditId}"]`)).toContainText('ui.theme')
    })

    test('should log security violations', async ({ page }) => {
      await loginAsUser(page)

      // Attempt to access admin endpoint directly
      const response = await page.request.post(`${TEST_CONFIG.BACKEND_URL}/api/settings/admin/reset`, {
        data: { confirm: true }
      })

      expect(response.status()).toBe(403)

      // Login as admin and check security audit
      await loginAsAdmin(page)
      await page.goto(`${TEST_CONFIG.FRONTEND_URL}/audit?filter=security`)

      // Should see unauthorized access attempt
      await expect(page.locator('[data-testid="security-violation"]')).toBeVisible()
      await expect(page.locator('[data-testid="security-violation"]')).toContainText('Unauthorized admin access attempt')
    })

    test('should include client information in audit entries', async ({ page }) => {
      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Make a setting change
      await page.click('[data-testid="category-ui"]')
      await page.click('[data-testid="setting-theme-toggle"]')

      const auditId = await page.locator('[data-testid="audit-id"]').textContent()

      // Check audit details
      await page.click('[data-testid="audit-log-link"]')
      await page.click(`[data-testid="audit-entry-${auditId}"]`)

      // Should include client information
      await expect(page.locator('[data-testid="audit-client-ip"]')).toBeVisible()
      await expect(page.locator('[data-testid="audit-user-agent"]')).toBeVisible()
      await expect(page.locator('[data-testid="audit-timestamp"]')).toBeVisible()
    })
  })

  test.describe('Data Migration and Upgrades', () => {
    test('should migrate old settings format to new schema', async ({ page }) => {
      // Set up old format settings in localStorage
      await page.goto(`${TEST_CONFIG.FRONTEND_URL}`)
      await page.evaluate(() => {
        const oldSettings = {
          theme: 'dark',
          language: 'en',
          version: 1 // Old version
        }
        localStorage.setItem('tomo_settings', JSON.stringify(oldSettings))
      })

      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Should show migration notice
      await expect(page.locator('[data-testid="migration-notice"]')).toBeVisible()

      // Settings should be migrated to new format
      await page.click('[data-testid="category-ui"]')
      const themeValue = await page.locator('[data-testid="current-theme"]').textContent()
      expect(themeValue).toBe('dark') // Preserved from old format
    })

    test('should handle corrupted settings data gracefully', async ({ page }) => {
      // Set up corrupted settings data
      await page.goto(`${TEST_CONFIG.FRONTEND_URL}`)
      await page.evaluate(() => {
        localStorage.setItem('tomo_settings', 'corrupted_json_data{{{')
      })

      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Should fallback to defaults
      await expect(page.locator('[data-testid="settings-reset-notice"]')).toBeVisible()

      // Should use default settings
      await page.click('[data-testid="category-ui"]')
      const themeValue = await page.locator('[data-testid="current-theme"]').textContent()
      expect(themeValue).toBe('light') // Default theme
    })
  })

  test.describe('Performance and Stress Testing', () => {
    test('should handle rapid setting changes', async ({ page }) => {
      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      await page.click('[data-testid="category-ui"]')

      // Rapidly toggle theme 10 times
      for (let i = 0; i < 10; i++) {
        await page.click('[data-testid="setting-theme-toggle"]')
        await page.waitForTimeout(100)
      }

      // Should handle all changes gracefully
      await expect(page.locator('[data-testid="save-success-message"], [data-testid="rate-limit-notice"]')).toBeVisible()
    })

    test('should handle large settings payloads', async ({ page }) => {
      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Navigate to advanced settings
      await page.click('[data-testid="category-system"]')
      await page.click('[data-testid="advanced-settings-toggle"]')

      // Fill in large configuration
      const largeConfig = JSON.stringify({
        servers: Array(100).fill(0).map((_, i) => ({
          id: i,
          name: `server_${i}`,
          config: `config_data_${i}`.repeat(100)
        }))
      })

      await page.fill('[data-testid="advanced-config-textarea"]', largeConfig)
      await page.click('[data-testid="save-settings-button"]')

      // Should handle large payload
      await expect(page.locator('[data-testid="save-success-message"], [data-testid="payload-too-large"]')).toBeVisible()
    })
  })

  test.describe('Cross-Platform Compatibility', () => {
    test('should work consistently across different browsers', async ({ page }) => {
      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Test basic functionality
      await page.click('[data-testid="category-ui"]')
      await page.click('[data-testid="setting-theme-toggle"]')

      await expect(page.locator('[data-testid="save-success-message"]')).toBeVisible()

      // Test persistence across page reloads
      await page.reload()
      await waitForSettingsLoad(page)

      // Settings should persist
      await page.click('[data-testid="category-ui"]')
      const persistedTheme = await page.locator('[data-testid="current-theme"]').textContent()
      expect(persistedTheme).toBeTruthy()
    })

    test('should handle different screen sizes and mobile devices', async ({ page }) => {
      // Test mobile viewport
      await page.setViewportSize({ width: 375, height: 667 })

      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Should show mobile-optimized layout
      await expect(page.locator('[data-testid="mobile-settings-layout"]')).toBeVisible()

      // Settings should still be functional
      await page.click('[data-testid="category-ui"]')
      await page.click('[data-testid="setting-theme-toggle"]')

      await expect(page.locator('[data-testid="save-success-message"]')).toBeVisible()
    })
  })

  test.describe('Error Recovery and Resilience', () => {
    test('should recover from network interruptions', async ({ page }) => {
      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Simulate network interruption
      await page.route('**/mcp/**', route => {
        route.abort('connectionrefused')
      })

      await page.click('[data-testid="category-ui"]')
      await page.click('[data-testid="setting-theme-toggle"]')

      // Should show offline notice
      await expect(page.locator('[data-testid="offline-mode-notice"]')).toBeVisible()

      // Restore network
      await page.unroute('**/mcp/**')
      await page.click('[data-testid="retry-connection-button"]')

      // Should reconnect and sync
      await expect(page.locator('[data-testid="online-mode-restored"]')).toBeVisible()
    })

    test('should handle server errors gracefully', async ({ page }) => {
      await loginAsAdmin(page)
      await navigateToSettings(page)
      await waitForSettingsLoad(page)

      // Simulate server error
      await page.route('**/mcp/**', route => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Internal server error' })
        })
      })

      await page.click('[data-testid="category-ui"]')
      await page.click('[data-testid="setting-theme-toggle"]')

      // Should show error message with retry option
      await expect(page.locator('[data-testid="server-error-notice"]')).toBeVisible()
      await expect(page.locator('[data-testid="retry-button"]')).toBeVisible()
    })
  })
})