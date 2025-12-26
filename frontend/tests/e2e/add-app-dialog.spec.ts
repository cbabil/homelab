/**
 * E2E tests for Add Custom Application dialog scroll behavior
 */

import { test, expect } from '@playwright/test'

test.describe('Add Custom Application Dialog', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/applications')
    await page.waitForLoadState('networkidle')
    
    // Wait for the page to load and become interactive
    await page.waitForSelector('text=Application Marketplace')
  })

  test('should open Add App dialog without vertical scroll bar', async ({ page }) => {
    // Click the Add App button
    const addButton = page.locator('button:has-text("Add App")')
    await expect(addButton).toBeVisible()
    await addButton.click()

    // Wait for dialog to appear
    const dialog = page.locator('[role="dialog"], .fixed.inset-0')
    await expect(dialog).toBeVisible()

    // Check dialog container
    const dialogContainer = page.locator('.bg-background.p-4.rounded-xl.border')
    await expect(dialogContainer).toBeVisible()

    // Verify no vertical scroll bar by checking overflow
    const hasScrollbar = await page.evaluate(() => {
      const dialog = document.querySelector('.bg-background.p-3.rounded-xl.border')
      if (!dialog) return false
      return dialog.scrollHeight > dialog.clientHeight
    })

    expect(hasScrollbar).toBe(false)
  })

  test('should display all form fields without scrolling', async ({ page }) => {
    // Open dialog
    await page.locator('button:has-text("Add App")').click()
    const dialog = page.locator('.bg-background.p-3.rounded-xl.border')
    await expect(dialog).toBeVisible()

    // Check that all key form fields are visible without scrolling
    await expect(page.locator('input[placeholder="Enter application name"]')).toBeVisible()
    await expect(page.locator('textarea[placeholder*="description"]')).toBeVisible()
    await expect(page.locator('input[placeholder="1.0.0"]')).toBeVisible()
    await expect(page.locator('select')).toBeVisible()
    await expect(page.locator('input[placeholder*="tags"]')).toBeVisible()
    await expect(page.locator('input[placeholder="Author name"]')).toBeVisible()
    await expect(page.locator('input[placeholder*="license"]')).toBeVisible()
    
    // System requirements section
    await expect(page.locator('input[placeholder*="RAM"]')).toBeVisible()
    await expect(page.locator('input[placeholder*="Storage"]')).toBeVisible()
    await expect(page.locator('input[placeholder*="ports"]')).toBeVisible()
    
    // Form buttons should be visible
    await expect(page.locator('button:has-text("Cancel")')).toBeVisible()
    await expect(page.locator('button:has-text("Add App")')).toBeVisible()
  })

  test('should close dialog when clicking Cancel', async ({ page }) => {
    // Open dialog
    await page.locator('button:has-text("Add App")').click()
    const dialog = page.locator('.bg-background.p-3.rounded-xl.border')
    await expect(dialog).toBeVisible()

    // Click Cancel
    await page.locator('button:has-text("Cancel")').click()
    await expect(dialog).not.toBeVisible()
  })

  test('should close dialog when clicking X button', async ({ page }) => {
    // Open dialog
    await page.locator('button:has-text("Add App")').click()
    const dialog = page.locator('.bg-background.p-3.rounded-xl.border')
    await expect(dialog).toBeVisible()

    // Click X button
    await page.locator('button').filter({ has: page.locator('svg') }).first().click()
    await expect(dialog).not.toBeVisible()
  })

  test('should work without scroll on laptop viewport (1280x720)', async ({ page }) => {
    // Set laptop viewport
    await page.setViewportSize({ width: 1280, height: 720 })
    
    // Open dialog and verify no scroll
    await page.locator('button:has-text("Add App")').click()
    const dialog = page.locator('.bg-background.p-3.rounded-xl.border')
    await expect(dialog).toBeVisible()

    const hasScrollbar = await page.evaluate(() => {
      const dialog = document.querySelector('.bg-background.p-3.rounded-xl.border')
      if (!dialog) return false
      return dialog.scrollHeight > dialog.clientHeight
    })

    expect(hasScrollbar).toBe(false)
  })

  test('should work without scroll on desktop viewport (1920x1080)', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 })
    
    // Open dialog and verify no scroll
    await page.locator('button:has-text("Add App")').click()
    const dialog = page.locator('.bg-background.p-3.rounded-xl.border')
    await expect(dialog).toBeVisible()

    const hasScrollbar = await page.evaluate(() => {
      const dialog = document.querySelector('.bg-background.p-3.rounded-xl.border')
      if (!dialog) return false
      return dialog.scrollHeight > dialog.clientHeight
    })

    expect(hasScrollbar).toBe(false)
  })
})