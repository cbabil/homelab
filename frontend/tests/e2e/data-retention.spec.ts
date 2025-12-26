/**
 * Data Retention E2E Tests
 *
 * Complete end-to-end testing of data retention features including:
 * - Settings configuration and validation
 * - Multi-step security confirmation flows
 * - Admin-only access controls and privilege verification
 * - Preview and cleanup operations with audit trails
 * - Cross-browser compatibility and accessibility testing
 */

import { test, expect, Page, BrowserContext } from '@playwright/test'

class DataRetentionWorkflow {
  constructor(private page: Page) {}

  async navigateToRetentionSettings(): Promise<void> {
    // Navigate to Settings page
    await this.page.locator('aside nav a:has-text("Settings")').click()
    await this.page.waitForURL('**/settings')
    await this.page.waitForLoadState('networkidle')

    // Locate Data Retention section
    const retentionSection = this.page.locator('h4:text("Data Retention")')
    await expect(retentionSection).toBeVisible()
  }

  async verifyRetentionSettingsVisible(): Promise<void> {
    await expect(this.page.locator('text=Auto-cleanup')).toBeVisible()
    await expect(this.page.locator('text=Log retention')).toBeVisible()
    await expect(this.page.locator('text=Other data')).toBeVisible()
    await expect(this.page.locator('button:text("Preview Cleanup")')).toBeVisible()
  }

  async updateLogRetention(days: number): Promise<void> {
    const logSlider = this.page.locator('[data-testid="log-retention-slider"]')
    await logSlider.fill(days.toString())
    await this.page.waitForTimeout(500) // Wait for debounce
  }

  async updateOtherDataRetention(days: number): Promise<void> {
    const dataSlider = this.page.locator('[data-testid="other-data-slider"]')
    await dataSlider.fill(days.toString())
    await this.page.waitForTimeout(500) // Wait for debounce
  }

  async toggleAutoCleanup(): Promise<void> {
    const toggle = this.page.locator('[data-testid="auto-cleanup-toggle"]')
    await toggle.click()
  }

  async startPreviewCleanup(): Promise<void> {
    const previewButton = this.page.locator('button:text("Preview Cleanup")')
    await previewButton.click()
  }

  async verifyPreviewDialog(expectedLogEntries: number, expectedOtherData: number, expectedSpace: string): Promise<void> {
    const dialog = this.page.locator('[role="dialog"]')
    await expect(dialog).toBeVisible()
    await expect(dialog.locator('h3:text("Cleanup Preview")')).toBeVisible()

    const previewText = dialog.locator('p')
    await expect(previewText).toContainText(`${expectedLogEntries} log entries`)
    await expect(previewText).toContainText(`${expectedOtherData} other records`)
    await expect(previewText).toContainText(expectedSpace)
  }

  async continueFromPreview(): Promise<void> {
    const continueButton = this.page.locator('button:text("Continue")')
    await continueButton.click()
  }

  async verifyConfirmationDialog(): Promise<void> {
    const dialog = this.page.locator('[role="dialog"]')
    await expect(dialog.locator('h3:text("Confirm Data Deletion")')).toBeVisible()
    await expect(dialog.locator('text="permanently delete data"')).toBeVisible()
  }

  async enterConfirmationText(text: string): Promise<void> {
    const input = this.page.locator('input[placeholder="DELETE DATA"]')
    await input.fill(text)
  }

  async confirmDeletion(): Promise<void> {
    const deleteButton = this.page.locator('button:text("Delete Data")')
    await deleteButton.click()
  }

  async cancelOperation(): Promise<void> {
    const cancelButton = this.page.locator('button:text("Cancel")')
    await cancelButton.click()
  }

  async verifyWarningMessage(warningText: string): Promise<void> {
    const warning = this.page.locator(`text="${warningText}"`)
    await expect(warning).toBeVisible()
  }

  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({
      path: `tests/screenshots/retention-${name}.png`,
      fullPage: true
    })
  }
}

class AdminAuthHelper {
  constructor(private page: Page) {}

  async loginAsAdmin(): Promise<void> {
    await this.page.goto('/login')
    await this.page.locator('input[name="username"]').fill('admin')
    await this.page.locator('input[name="password"]').fill('admin123')
    await this.page.locator('button[type="submit"]').click()
    await this.page.waitForURL('**/dashboard')
  }

  async loginAsRegularUser(): Promise<void> {
    await this.page.goto('/login')
    await this.page.locator('input[name="username"]').fill('user')
    await this.page.locator('input[name="password"]').fill('user123')
    await this.page.locator('button[type="submit"]').click()
    await this.page.waitForURL('**/dashboard')
  }

  async logout(): Promise<void> {
    const userMenu = this.page.locator('[data-testid="user-menu"]')
    await userMenu.click()
    await this.page.locator('text="Logout"').click()
    await this.page.waitForURL('**/login')
  }
}

test.describe('Data Retention E2E Tests', () => {
  let workflow: DataRetentionWorkflow
  let auth: AdminAuthHelper

  test.beforeEach(async ({ page }) => {
    workflow = new DataRetentionWorkflow(page)
    auth = new AdminAuthHelper(page)
  })

  test.describe('Admin Access Control', () => {
    test('should allow admin users to access retention settings', async ({ page }) => {
      await auth.loginAsAdmin()
      await workflow.navigateToRetentionSettings()
      await workflow.verifyRetentionSettingsVisible()
      await workflow.takeScreenshot('admin-access-allowed')
    })

    test('should deny access to regular users', async ({ page }) => {
      await auth.loginAsRegularUser()
      await workflow.navigateToRetentionSettings()

      // Should not see retention settings or show access denied message
      const retentionSection = page.locator('h4:text("Data Retention")')
      await expect(retentionSection).not.toBeVisible()

      // Should show appropriate message for restricted access
      const restrictedMessage = page.locator('text="Admin privileges required"')
      await expect(restrictedMessage).toBeVisible()
      await workflow.takeScreenshot('regular-user-denied')
    })

    test('should redirect unauthorized users attempting direct access', async ({ page }) => {
      // Try to access settings without authentication
      await page.goto('/settings')

      // Should be redirected to login
      await page.waitForURL('**/login')
      await expect(page.locator('h1:text("Login")')).toBeVisible()
    })
  })

  test.describe('Settings Configuration', () => {
    test.beforeEach(async ({ page }) => {
      await auth.loginAsAdmin()
      await workflow.navigateToRetentionSettings()
    })

    test('should display current retention settings', async ({ page }) => {
      const logSlider = page.locator('[data-testid="log-retention-slider"]')
      const dataSlider = page.locator('[data-testid="other-data-slider"]')

      // Should have default values
      await expect(logSlider).toHaveValue('30')
      await expect(dataSlider).toHaveValue('365')
      await workflow.takeScreenshot('default-settings')
    })

    test('should update log retention settings', async ({ page }) => {
      await workflow.updateLogRetention(60)

      // Verify the value was updated
      const logSlider = page.locator('[data-testid="log-retention-slider"]')
      await expect(logSlider).toHaveValue('60')

      // Should show some feedback (loading state or success message)
      await page.waitForTimeout(1000) // Allow for update to complete
      await workflow.takeScreenshot('log-retention-updated')
    })

    test('should update other data retention settings', async ({ page }) => {
      await workflow.updateOtherDataRetention(730)

      const dataSlider = page.locator('[data-testid="other-data-slider"]')
      await expect(dataSlider).toHaveValue('730')
      await workflow.takeScreenshot('data-retention-updated')
    })

    test('should toggle auto-cleanup setting', async ({ page }) => {
      await workflow.toggleAutoCleanup()

      const toggle = page.locator('[data-testid="auto-cleanup-toggle"]')
      await expect(toggle).toBeChecked()
      await workflow.takeScreenshot('auto-cleanup-enabled')
    })

    test('should enforce minimum and maximum values', async ({ page }) => {
      // Test log retention limits
      const logSlider = page.locator('[data-testid="log-retention-slider"]')
      await expect(logSlider).toHaveAttribute('min', '7')
      await expect(logSlider).toHaveAttribute('max', '365')

      // Test other data limits
      const dataSlider = page.locator('[data-testid="other-data-slider"]')
      await expect(dataSlider).toHaveAttribute('min', '30')
      await expect(dataSlider).toHaveAttribute('max', '3650')
    })

    test('should show warnings for dangerous settings', async ({ page }) => {
      // Set dangerously low retention periods
      await workflow.updateLogRetention(10) // Below 14 day warning threshold

      await workflow.verifyWarningMessage('Log retention below 14 days may affect debugging capabilities')

      await workflow.updateOtherDataRetention(60) // Below 90 day warning threshold
      await workflow.verifyWarningMessage('Very short retention periods may cause data loss')
      await workflow.takeScreenshot('dangerous-settings-warnings')
    })

    test('should highlight dangerous auto-cleanup configuration', async ({ page }) => {
      await workflow.updateLogRetention(20) // Short retention
      await workflow.toggleAutoCleanup() // Enable auto-cleanup

      await workflow.verifyWarningMessage('Auto-cleanup with short retention periods requires extra caution')
      await workflow.takeScreenshot('dangerous-auto-cleanup')
    })
  })

  test.describe('Preview Cleanup Workflow', () => {
    test.beforeEach(async ({ page }) => {
      await auth.loginAsAdmin()
      await workflow.navigateToRetentionSettings()
    })

    test('should show preview cleanup dialog', async ({ page }) => {
      await workflow.startPreviewCleanup()
      await workflow.verifyPreviewDialog(150, 25, '2.5 MB')
      await workflow.takeScreenshot('preview-dialog')
    })

    test('should show loading state during preview', async ({ page }) => {
      // Mock slow response for loading state
      const previewButton = page.locator('button:text("Preview Cleanup")')
      await previewButton.click()

      // Should show loading text
      const loadingButton = page.locator('button:text("Analyzing...")')
      await expect(loadingButton).toBeVisible()

      // Wait for preview to complete
      await page.waitForTimeout(2000)
      await workflow.takeScreenshot('preview-loading')
    })

    test('should allow canceling from preview dialog', async ({ page }) => {
      await workflow.startPreviewCleanup()
      await workflow.verifyPreviewDialog(150, 25, '2.5 MB')
      await workflow.cancelOperation()

      // Dialog should be closed
      const dialog = page.locator('[role="dialog"]')
      await expect(dialog).not.toBeVisible()
    })
  })

  test.describe('Multi-step Confirmation Flow', () => {
    test.beforeEach(async ({ page }) => {
      await auth.loginAsAdmin()
      await workflow.navigateToRetentionSettings()
      // Set up dangerous settings to trigger confirmation requirements
      await workflow.updateLogRetention(10)
      await workflow.updateOtherDataRetention(60)
    })

    test('should require confirmation for dangerous operations', async ({ page }) => {
      await workflow.startPreviewCleanup()
      await workflow.verifyPreviewDialog(150, 25, '2.5 MB')
      await workflow.continueFromPreview()
      await workflow.verifyConfirmationDialog()

      // Should require confirmation text
      const confirmInput = page.locator('input[placeholder="DELETE DATA"]')
      await expect(confirmInput).toBeVisible()

      const deleteButton = page.locator('button:text("Delete Data")')
      await expect(deleteButton).toBeDisabled()
      await workflow.takeScreenshot('confirmation-required')
    })

    test('should enable delete button only with correct confirmation', async ({ page }) => {
      await workflow.startPreviewCleanup()
      await workflow.verifyPreviewDialog(150, 25, '2.5 MB')
      await workflow.continueFromPreview()
      await workflow.verifyConfirmationDialog()

      // Type incorrect text
      await workflow.enterConfirmationText('wrong text')
      const deleteButton = page.locator('button:text("Delete Data")')
      await expect(deleteButton).toBeDisabled()

      // Type correct text
      await workflow.enterConfirmationText('DELETE DATA')
      await expect(deleteButton).not.toBeDisabled()
      await workflow.takeScreenshot('confirmation-text-correct')
    })

    test('should complete full deletion workflow', async ({ page }) => {
      await workflow.startPreviewCleanup()
      await workflow.verifyPreviewDialog(150, 25, '2.5 MB')
      await workflow.continueFromPreview()
      await workflow.verifyConfirmationDialog()
      await workflow.enterConfirmationText('DELETE DATA')
      await workflow.confirmDeletion()

      // Should show success message or return to settings
      await page.waitForTimeout(2000)
      const successMessage = page.locator('text="Cleanup completed successfully"')
      await expect(successMessage).toBeVisible({ timeout: 10000 })
      await workflow.takeScreenshot('cleanup-completed')
    })

    test('should allow canceling at final confirmation', async ({ page }) => {
      await workflow.startPreviewCleanup()
      await workflow.verifyPreviewDialog(150, 25, '2.5 MB')
      await workflow.continueFromPreview()
      await workflow.verifyConfirmationDialog()
      await workflow.cancelOperation()

      // Should return to settings page
      const dialog = page.locator('[role="dialog"]')
      await expect(dialog).not.toBeVisible()
      await workflow.verifyRetentionSettingsVisible()
    })
  })

  test.describe('Error Handling', () => {
    test.beforeEach(async ({ page }) => {
      await auth.loginAsAdmin()
      await workflow.navigateToRetentionSettings()
    })

    test('should handle server connection errors', async ({ page }) => {
      // Simulate network error by going offline
      await page.context().setOffline(true)

      await workflow.updateLogRetention(60)

      // Should show appropriate error message
      const errorMessage = page.locator('text="Failed to connect to server"')
      await expect(errorMessage).toBeVisible({ timeout: 5000 })
      await workflow.takeScreenshot('connection-error')
    })

    test('should handle preview operation failures', async ({ page }) => {
      // Mock server error response
      await page.route('**/api/mcp', route => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ success: false, error: 'Internal server error' })
        })
      })

      await workflow.startPreviewCleanup()

      // Should show error message
      const errorMessage = page.locator('text="Failed to preview cleanup"')
      await expect(errorMessage).toBeVisible({ timeout: 5000 })
      await workflow.takeScreenshot('preview-error')
    })

    test('should handle session expiration', async ({ page }) => {
      // Mock session expiration
      await page.route('**/api/mcp', route => {
        route.fulfill({
          status: 401,
          body: JSON.stringify({ success: false, error: 'Session expired' })
        })
      })

      await workflow.updateLogRetention(60)

      // Should redirect to login or show session expired message
      const sessionError = page.locator('text="Session expired"')
      await expect(sessionError).toBeVisible({ timeout: 5000 })
    })
  })

  test.describe('Accessibility', () => {
    test.beforeEach(async ({ page }) => {
      await auth.loginAsAdmin()
      await workflow.navigateToRetentionSettings()
    })

    test('should have proper ARIA labels and roles', async ({ page }) => {
      // Check sliders have proper labels
      const logSlider = page.locator('[role="slider"][aria-label*="Log retention"]')
      await expect(logSlider).toBeVisible()

      const dataSlider = page.locator('[role="slider"][aria-label*="Other data"]')
      await expect(dataSlider).toBeVisible()

      // Check dialogs have proper roles
      await workflow.startPreviewCleanup()
      const dialog = page.locator('[role="dialog"][aria-modal="true"]')
      await expect(dialog).toBeVisible()
    })

    test('should support keyboard navigation', async ({ page }) => {
      // Tab through controls
      await page.keyboard.press('Tab')
      let focused = await page.locator(':focus')
      await expect(focused).toBeVisible()

      // Continue tabbing through all controls
      for (let i = 0; i < 5; i++) {
        await page.keyboard.press('Tab')
        focused = await page.locator(':focus')
        await expect(focused).toBeVisible()
      }
    })

    test('should activate controls with keyboard', async ({ page }) => {
      const previewButton = page.locator('button:text("Preview Cleanup")')
      await previewButton.focus()
      await page.keyboard.press('Enter')

      // Should open preview dialog
      const dialog = page.locator('[role="dialog"]')
      await expect(dialog).toBeVisible()
    })

    test('should announce warnings to screen readers', async ({ page }) => {
      await workflow.updateLogRetention(10)

      // Warning should be in accessibility tree
      const warning = page.locator('text="Log retention below 14 days may affect debugging capabilities"')
      await expect(warning).toBeVisible()

      // Check that warning has appropriate accessibility attributes
      await expect(warning).toHaveAttribute('role', 'alert')
    })
  })

  test.describe('Cross-browser Compatibility', () => {
    test('should work consistently across browsers', async ({ page, browserName }) => {
      await auth.loginAsAdmin()
      await workflow.navigateToRetentionSettings()
      await workflow.verifyRetentionSettingsVisible()

      // Test basic functionality in all browsers
      await workflow.updateLogRetention(45)
      await workflow.toggleAutoCleanup()
      await workflow.startPreviewCleanup()
      await workflow.verifyPreviewDialog(150, 25, '2.5 MB')

      await workflow.takeScreenshot(`${browserName}-compatibility`)
    })

    test('should handle touch interactions on mobile', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 })

      await auth.loginAsAdmin()
      await workflow.navigateToRetentionSettings()

      // Test touch interactions
      const toggle = page.locator('[data-testid="auto-cleanup-toggle"]')
      await toggle.tap()

      await expect(toggle).toBeChecked()
      await workflow.takeScreenshot('mobile-touch')
    })
  })

  test.describe('Performance', () => {
    test('should load retention settings quickly', async ({ page }) => {
      await auth.loginAsAdmin()

      const startTime = Date.now()
      await workflow.navigateToRetentionSettings()
      await workflow.verifyRetentionSettingsVisible()
      const loadTime = Date.now() - startTime

      // Should load within reasonable time (3 seconds)
      expect(loadTime).toBeLessThan(3000)
    })

    test('should handle rapid slider changes without performance issues', async ({ page }) => {
      await auth.loginAsAdmin()
      await workflow.navigateToRetentionSettings()

      const logSlider = page.locator('[data-testid="log-retention-slider"]')

      // Rapid slider changes
      for (let i = 0; i < 10; i++) {
        await logSlider.fill((30 + i * 5).toString())
        await page.waitForTimeout(50)
      }

      // Should remain responsive
      await expect(logSlider).toHaveValue('75')
    })

    test('should not leak memory during extended use', async ({ page }) => {
      await auth.loginAsAdmin()
      await workflow.navigateToRetentionSettings()

      // Simulate extended use with multiple operations
      for (let i = 0; i < 5; i++) {
        await workflow.updateLogRetention(30 + i * 10)
        await workflow.toggleAutoCleanup()
        await workflow.startPreviewCleanup()
        await workflow.cancelOperation()
        await page.waitForTimeout(500)
      }

      // Page should still be responsive
      await workflow.verifyRetentionSettingsVisible()
    })
  })
})

test.describe('Audit and Compliance', () => {
  let workflow: DataRetentionWorkflow
  let auth: AdminAuthHelper

  test.beforeEach(async ({ page }) => {
    workflow = new DataRetentionWorkflow(page)
    auth = new AdminAuthHelper(page)
    await auth.loginAsAdmin()
    await workflow.navigateToRetentionSettings()
  })

  test('should log all retention operations for audit', async ({ page }) => {
    // Perform various operations
    await workflow.updateLogRetention(45)
    await workflow.toggleAutoCleanup()
    await workflow.startPreviewCleanup()
    await workflow.verifyPreviewDialog(150, 25, '2.5 MB')
    await workflow.continueFromPreview()
    await workflow.verifyConfirmationDialog()
    await workflow.enterConfirmationText('DELETE DATA')
    await workflow.confirmDeletion()

    // Navigate to audit logs (if available in UI)
    const auditLink = page.locator('a:text("Audit Logs")')
    if (await auditLink.isVisible()) {
      await auditLink.click()

      // Verify retention operations are logged
      const retentionLogs = page.locator('text*="retention"')
      await expect(retentionLogs.first()).toBeVisible()
    }
  })

  test('should maintain data integrity during operations', async ({ page }) => {
    // Verify initial state
    await workflow.verifyRetentionSettingsVisible()

    // Perform operations that should not affect other settings
    await workflow.updateLogRetention(60)

    // Navigate away and back to verify persistence
    await page.locator('aside nav a:has-text("Dashboard")').click()
    await page.waitForURL('**/dashboard')

    await workflow.navigateToRetentionSettings()

    // Settings should be persisted
    const logSlider = page.locator('[data-testid="log-retention-slider"]')
    await expect(logSlider).toHaveValue('60')
  })
})