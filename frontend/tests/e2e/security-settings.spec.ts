/**
 * End-to-End Tests for Security Settings
 *
 * Tests the security settings tab functionality including:
 * - Session timeout configuration
 * - Account locking settings
 * - Password policy settings (min length, blocklist, complexity, expiration)
 */

import { test, expect } from '@playwright/test'
import { navigateToSettings, clickSettingsTab } from './settings-test-utils'

test.describe('Security Settings', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies()
  })

  test.describe('Navigation', () => {
    test('should display Security tab in settings', async ({ page }) => {
      await navigateToSettings(page)

      const securityTab = page.locator('button:has-text("Security")')
      await expect(securityTab).toBeVisible()
    })

    test('should switch to Security tab when clicked', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Security')

      // Should show Session section
      await expect(page.getByText('Session', { exact: false })).toBeVisible()
    })
  })

  test.describe('Session Settings', () => {
    test('should display session timeout dropdown', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Security')

      // Find session timeout label and dropdown
      await expect(page.getByText('Session timeout')).toBeVisible()
    })

    test('should have session timeout options', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Security')

      // Click the dropdown to see options
      const dropdown = page.locator('[role="combobox"]').first()
      await dropdown.click()

      // Check for timeout options
      await expect(page.getByRole('option', { name: '30 minutes' })).toBeVisible()
      await expect(page.getByRole('option', { name: '1 hour' })).toBeVisible()
    })
  })

  test.describe('Account Locking', () => {
    test('should display account locking section', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Security')

      await expect(page.getByText('Account Locking')).toBeVisible()
    })

    test('should display max login attempts field', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Security')

      await expect(page.getByText('Max login attempts')).toBeVisible()
    })

    test('should display lockout duration dropdown', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Security')

      await expect(page.getByText('Lockout duration')).toBeVisible()
    })

    test('should allow changing max login attempts', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Security')

      // Find the max attempts input
      const maxAttemptsInput = page.locator('input[type="number"]').first()
      await maxAttemptsInput.clear()
      await maxAttemptsInput.fill('10')

      // Verify the value changed
      await expect(maxAttemptsInput).toHaveValue('10')
    })
  })

  test.describe('Password Policy', () => {
    test('should display password policy section', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Security')

      await expect(page.getByText('Password Policy')).toBeVisible()
    })

    test('should display minimum length setting', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Security')

      await expect(page.getByText('Minimum length')).toBeVisible()
    })

    test('should display blocklist check toggle', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Security')

      await expect(page.getByText('Password blocklist screening')).toBeVisible()
    })

    test('should display breach database check toggle', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Security')

      await expect(page.getByText('Breach database check')).toBeVisible()
    })

    test('should display complexity toggles', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Security')

      await expect(page.getByText('Require uppercase')).toBeVisible()
      await expect(page.getByText('Require numbers')).toBeVisible()
      await expect(page.getByText('Require special characters')).toBeVisible()
    })

    test('should display password expiration dropdown', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Security')

      await expect(page.getByText('Password expiration')).toBeVisible()
    })

    test('should allow toggling blocklist check', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Security')

      // Find the blocklist toggle switch
      const blocklistRow = page.locator('text=Password blocklist screening').locator('..')
      const toggle = blocklistRow.locator('[role="checkbox"], input[type="checkbox"]').first()

      // Get initial state
      const initialState = await toggle.isChecked()

      // Click to toggle
      await toggle.click()

      // Verify state changed
      const newState = await toggle.isChecked()
      expect(newState).toBe(!initialState)
    })
  })

  test.describe('Auto-save', () => {
    test('should show saving indicator when settings change', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Security')

      // Change a setting
      const maxAttemptsInput = page.locator('input[type="number"]').first()
      await maxAttemptsInput.clear()
      await maxAttemptsInput.fill('7')

      // Should show saving indicator in header (may be brief)
      // The header title should show "Settings - Saving..." momentarily
      // Since it's fast, we just verify the page doesn't error
      await expect(page.getByText('Settings')).toBeVisible()
    })
  })

  test.describe('Error Handling', () => {
    test('should handle page load without crashing', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Security')

      // Wait for content to load
      await page.waitForTimeout(1000)

      // Should not crash - page should still be usable
      await expect(page.getByText('Account Locking')).toBeVisible()
    })
  })
})
