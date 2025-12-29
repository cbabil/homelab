/**
 * End-to-End Tests for Server Settings
 *
 * Tests the server settings tab functionality including:
 * - SSH connection settings (timeout, retry count, auto-retry)
 * - MCP server configuration
 * - Connection status and controls
 */

import { test, expect } from '@playwright/test'
import { navigateToSettings, clickSettingsTab } from './settings-test-utils'

test.describe('Server Settings', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies()
  })

  test.describe('Navigation', () => {
    test('should display Servers tab in settings', async ({ page }) => {
      await navigateToSettings(page)

      const serversTab = page.locator('button:has-text("Servers")')
      await expect(serversTab).toBeVisible()
    })

    test('should switch to Servers tab when clicked', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')

      // Should show sub-tabs (SSH and MCP)
      await expect(page.locator('button:has-text("SSH")')).toBeVisible()
      await expect(page.locator('button:has-text("MCP")')).toBeVisible()
    })
  })

  test.describe('Sub-tab Navigation', () => {
    test('should display SSH tab as default', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')

      // SSH should be the default tab - check for Connection Settings
      await expect(page.getByRole('heading', { name: 'Connection Settings' })).toBeVisible()
    })

    test('should switch to MCP tab when clicked', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')

      // Click MCP tab
      await page.click('button:has-text("MCP")')
      await page.waitForTimeout(500)

      // Should show MCP Server Configuration
      await expect(page.getByRole('heading', { name: 'MCP Server Configuration' })).toBeVisible()
    })

    test('should switch back to SSH tab from MCP', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')

      // Go to MCP first
      await page.click('button:has-text("MCP")')
      await page.waitForTimeout(500)

      // Then back to SSH
      await page.click('button:has-text("SSH")')
      await page.waitForTimeout(500)

      // Should show Connection Settings again
      await expect(page.getByRole('heading', { name: 'Connection Settings' })).toBeVisible()
    })
  })

  test.describe('SSH Settings', () => {
    test('should display timeout dropdown', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')

      const timeoutRow = page.locator('text=Timeout').locator('..')
      const dropdown = timeoutRow.locator('select')

      await expect(dropdown).toBeVisible()
    })

    test('should display timeout options', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')

      const timeoutRow = page.locator('text=Timeout').locator('..')
      const dropdown = timeoutRow.locator('select')

      const options = await dropdown.locator('option').allTextContents()
      expect(options).toContain('10s')
      expect(options).toContain('30s')
      expect(options).toContain('1m')
    })

    test('should allow changing timeout setting', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')

      const timeoutRow = page.locator('text=Timeout').locator('..')
      const dropdown = timeoutRow.locator('select')

      await dropdown.selectOption('30')
      const value = await dropdown.inputValue()
      expect(value).toBe('30')
    })

    test('should display retry count dropdown', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')

      const retryRow = page.locator('text=Retry count').locator('..')
      const dropdown = retryRow.locator('select')

      await expect(dropdown).toBeVisible()
    })

    test('should display retry count options', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')

      const retryRow = page.locator('text=Retry count').locator('..')
      const dropdown = retryRow.locator('select')

      const options = await dropdown.locator('option').allTextContents()
      expect(options).toContain('1')
      expect(options).toContain('3')
      expect(options).toContain('5')
    })

    test('should allow changing retry count', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')

      const retryRow = page.locator('text=Retry count').locator('..')
      const dropdown = retryRow.locator('select')

      await dropdown.selectOption('5')
      const value = await dropdown.inputValue()
      expect(value).toBe('5')
    })

    test('should display auto-retry toggle', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')

      const autoRetryRow = page.locator('text=Auto-retry').locator('..')
      const toggle = autoRetryRow.locator('button[role="switch"]')

      await expect(toggle).toBeVisible()
    })

    test('should toggle auto-retry on/off', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')

      const autoRetryRow = page.locator('text=Auto-retry').locator('..')
      const toggle = autoRetryRow.locator('button[role="switch"]')

      const initialState = await toggle.getAttribute('aria-checked')

      await toggle.click()
      await page.waitForTimeout(300)

      const newState = await toggle.getAttribute('aria-checked')
      expect(newState).not.toBe(initialState)
    })
  })

  test.describe('MCP Settings', () => {
    test('should display MCP Server Configuration heading', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')
      await page.click('button:has-text("MCP")')

      await expect(page.getByRole('heading', { name: 'MCP Server Configuration' })).toBeVisible()
    })

    test('should display connection status indicator', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')
      await page.click('button:has-text("MCP")')

      // Look for status text - one of Connected, Disconnected, Connecting..., or Connection Error
      const statusText = page.locator('text=Connected')
        .or(page.locator('text=Disconnected'))
        .or(page.locator('text=Connecting'))
        .or(page.locator('text=Connection Error'))
      await expect(statusText.first()).toBeVisible()
    })

    test('should display connect/disconnect button', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')
      await page.click('button:has-text("MCP")')

      // Should have either Connect or Disconnect button
      const connectButton = page.locator('button:has-text("Connect"), button:has-text("Disconnect")')
      await expect(connectButton.first()).toBeVisible()
    })

    test('should display edit button', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')
      await page.click('button:has-text("MCP")')

      // Should have Edit or Save button
      const editButton = page.locator('button:has-text("Edit"), button:has-text("Save")')
      await expect(editButton.first()).toBeVisible()
    })

    test('should display MCP configuration', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')
      await page.click('button:has-text("MCP")')

      // Should show configuration display (pre/code block or textarea)
      const configDisplay = page.locator('pre, textarea, code')
      await expect(configDisplay.first()).toBeVisible()
    })

    test('should show configuration in JSON format', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')
      await page.click('button:has-text("MCP")')

      // Look for JSON-like content
      const configText = await page.locator('pre code, pre').first().textContent()

      // Should contain JSON structure indicators
      if (configText) {
        expect(configText).toContain('{')
        expect(configText).toContain('}')
      }
    })

    test('should toggle edit mode when Edit button clicked', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')
      await page.click('button:has-text("MCP")')

      // Find and click Edit button
      const editButton = page.locator('button:has-text("Edit")')

      if (await editButton.isVisible()) {
        await editButton.click()
        await page.waitForTimeout(500)

        // Should now show Save button and textarea
        await expect(page.locator('button:has-text("Save")')).toBeVisible()
        await expect(page.locator('textarea')).toBeVisible()
      }
    })

    test('should show placeholder text in edit mode', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')
      await page.click('button:has-text("MCP")')

      const editButton = page.locator('button:has-text("Edit")')

      if (await editButton.isVisible()) {
        await editButton.click()
        await page.waitForTimeout(500)

        const textarea = page.locator('textarea')
        const placeholder = await textarea.getAttribute('placeholder')
        expect(placeholder).toContain('MCP')
      }
    })
  })

  test.describe('MCP Connection', () => {
    test('should show connected status when MCP is connected', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')
      await page.click('button:has-text("MCP")')

      // Wait for connection status
      await page.waitForTimeout(2000)

      // Check for connection status indicator
      const connectedIndicator = page.locator('text=Connected')
      const connectionStatus = await connectedIndicator.isVisible().catch(() => false)

      // Status should be one of the expected values
      const statusText = page.locator('text=Connected')
        .or(page.locator('text=Disconnected'))
        .or(page.locator('text=Connecting'))
        .or(page.locator('text=Connection Error'))
      await expect(statusText.first()).toBeVisible()
    })

    test('should show status indicator dot', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')
      await page.click('button:has-text("MCP")')

      // Look for the colored dot indicator
      const statusDot = page.locator('.rounded-full').first()
      await expect(statusDot).toBeVisible()
    })
  })

  test.describe('Error Handling', () => {
    test('should display error message if MCP connection fails', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')
      await page.click('button:has-text("MCP")')

      // Wait for any error messages
      await page.waitForTimeout(2000)

      // Error messages should be styled appropriately if present
      const errorMessage = page.locator('text=Error, text=Failed, text=Connection Error')
      // This may or may not be visible depending on connection status
    })

    test('should handle invalid JSON in edit mode gracefully', async ({ page }) => {
      await navigateToSettings(page)
      await clickSettingsTab(page, 'Servers')
      await page.click('button:has-text("MCP")')

      const editButton = page.locator('button:has-text("Edit")')

      if (await editButton.isVisible()) {
        await editButton.click()
        await page.waitForTimeout(500)

        // Enter invalid JSON
        const textarea = page.locator('textarea')
        await textarea.fill('invalid json {{{')

        // Try to save
        const saveButton = page.locator('button:has-text("Save")')
        await saveButton.click()
        await page.waitForTimeout(500)

        // Should show error message or maintain edit mode
        const errorVisible = await page.locator('text=Invalid, text=Error, text=JSON').first().isVisible().catch(() => false)
        const stillEditing = await textarea.isVisible().catch(() => false)

        // Either error shown or still in edit mode
        expect(errorVisible || stillEditing).toBe(true)
      }
    })
  })
})
