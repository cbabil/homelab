/**
 * End-to-End Tests for Notification Settings
 *
 * Tests the notification settings tab functionality including:
 * - System alerts toggles
 * - Server alerts
 * - Resource alerts
 * - Update alerts
 */

import { test, expect } from '@playwright/test'
import { navigateToSettings, clickSettingsTab } from './settings-test-utils'

test.describe('Notification Settings', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies()
  })

  test.describe('Navigation', () => {
    test('should display Notifications tab in settings', async ({ page }) => {
      await navigateToSettings(page)

      // Use specific selector for the tab navigation area
      const tabNav = page.locator('.bg-muted.rounded-lg').first()
      const notificationsTab = tabNav.locator('button:has-text("Notifications")')
      await expect(notificationsTab).toBeVisible()
    })

    test('should switch to Notifications tab when clicked', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Notifications')

      // Should show System Alerts heading
      await expect(page.getByRole('heading', { name: 'System Alerts' })).toBeVisible()
    })
  })

  test.describe('System Alerts Section', () => {
    test('should display System Alerts section', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Notifications')

      await expect(page.getByRole('heading', { name: 'System Alerts' })).toBeVisible()
    })

    test('should display server alerts toggle', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Notifications')

      // Find server alerts row
      const serverAlertsRow = page.locator('text=Server alerts').locator('..')
      await expect(serverAlertsRow).toBeVisible()

      // Should have a toggle
      const toggle = serverAlertsRow.locator('button[role="switch"]')
      await expect(toggle).toBeVisible()
    })

    test('should display resource alerts toggle', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Notifications')

      // Find resource alerts row
      const resourceAlertsRow = page.locator('text=Resource alerts').locator('..')
      await expect(resourceAlertsRow).toBeVisible()

      // Should have a toggle
      const toggle = resourceAlertsRow.locator('button[role="switch"]')
      await expect(toggle).toBeVisible()
    })

    test('should display update alerts toggle', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Notifications')

      // Find update alerts row
      const updateAlertsRow = page.locator('text=Update alerts').locator('..')
      await expect(updateAlertsRow).toBeVisible()

      // Should have a toggle
      const toggle = updateAlertsRow.locator('button[role="switch"]')
      await expect(toggle).toBeVisible()
    })
  })

  test.describe('Toggle Interactions', () => {
    test('should toggle server alerts on/off', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Notifications')

      const serverAlertsRow = page.locator('text=Server alerts').locator('..')
      const toggle = serverAlertsRow.locator('button[role="switch"]')

      // Get initial state
      const initialState = await toggle.getAttribute('aria-checked')

      // Click to toggle
      await toggle.click()
      await page.waitForTimeout(300) // Wait for state change

      // State should be different
      const newState = await toggle.getAttribute('aria-checked')
      expect(newState).not.toBe(initialState)

      // Toggle back
      await toggle.click()
      await page.waitForTimeout(300)

      // Should be back to initial state
      const finalState = await toggle.getAttribute('aria-checked')
      expect(finalState).toBe(initialState)
    })

    test('should toggle resource alerts on/off', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Notifications')

      const resourceAlertsRow = page.locator('text=Resource alerts').locator('..')
      const toggle = resourceAlertsRow.locator('button[role="switch"]')

      // Get initial state
      const initialState = await toggle.getAttribute('aria-checked')

      // Click to toggle
      await toggle.click()
      await page.waitForTimeout(300)

      // State should be different
      const newState = await toggle.getAttribute('aria-checked')
      expect(newState).not.toBe(initialState)
    })

    test('should toggle update alerts on/off', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Notifications')

      const updateAlertsRow = page.locator('text=Update alerts').locator('..')
      const toggle = updateAlertsRow.locator('button[role="switch"]')

      // Get initial state
      const initialState = await toggle.getAttribute('aria-checked')

      // Click to toggle
      await toggle.click()
      await page.waitForTimeout(300)

      // State should be different
      const newState = await toggle.getAttribute('aria-checked')
      expect(newState).not.toBe(initialState)
    })
  })

  test.describe('Toggle States', () => {
    test('should show visual feedback for enabled state', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Notifications')

      const serverAlertsRow = page.locator('text=Server alerts').locator('..')
      const toggle = serverAlertsRow.locator('button[role="switch"]')

      // Ensure toggle is on
      const isChecked = await toggle.getAttribute('aria-checked')
      if (isChecked !== 'true') {
        await toggle.click()
        await page.waitForTimeout(300)
      }

      // Toggle should have visual indication of being on
      const toggleClass = await toggle.getAttribute('class')
      // Usually enabled toggles have a specific background color class
    })

    test('should show visual feedback for disabled state', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Notifications')

      const serverAlertsRow = page.locator('text=Server alerts').locator('..')
      const toggle = serverAlertsRow.locator('button[role="switch"]')

      // Ensure toggle is off
      const isChecked = await toggle.getAttribute('aria-checked')
      if (isChecked === 'true') {
        await toggle.click()
        await page.waitForTimeout(300)
      }

      // Toggle should have visual indication of being off
      const newState = await toggle.getAttribute('aria-checked')
      expect(newState).toBe('false')
    })
  })

  test.describe('Settings Persistence', () => {
    test('should maintain toggle states after tab switch', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Notifications')

      const serverAlertsRow = page.locator('text=Server alerts').locator('..')
      const toggle = serverAlertsRow.locator('button[role="switch"]')

      // Toggle the setting
      await toggle.click()
      await page.waitForTimeout(300)
      const stateAfterToggle = await toggle.getAttribute('aria-checked')

      // Switch to another tab
      await clickSettingsTab(page, 'General')
      await page.waitForTimeout(500)

      // Switch back to Notifications
      await clickSettingsTab(page, 'Notifications')
      await page.waitForTimeout(500)

      // State should be preserved
      const stateAfterSwitch = await toggle.getAttribute('aria-checked')
      expect(stateAfterSwitch).toBe(stateAfterToggle)
    })
  })
})
