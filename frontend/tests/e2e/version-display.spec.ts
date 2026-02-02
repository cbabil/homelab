/**
 * Version Display E2E Tests
 * 
 * Focused tests specifically for the version display functionality
 * in the sidebar navigation footer.
 */

import { test, expect } from '@playwright/test'

test.describe('Version Display in Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Clear any existing authentication state
    await page.context().clearCookies()
    try {
      await page.evaluate(() => {
        localStorage.clear()
        sessionStorage.clear()
      })
    } catch (e) {
      // Some browsers may not allow localStorage access on certain origins
      console.log('localStorage clear failed:', e)
    }
  })

  test('should display version after successful login', async ({ page }) => {
    // Start by going to the app (will redirect to login if not authenticated)
    await page.goto('/')
    
    // Should be redirected to login page
    await expect(page).toHaveURL(/\/login/)
    
    // Wait for login page to load
    await page.waitForLoadState('networkidle')
    
    // Fill in admin credentials and submit
    await page.fill('input[autocomplete="username"]', 'admin')
    await page.fill('input[autocomplete="current-password"]', 'TomoAdmin123!')
    await page.click('button[type="submit"]')
    
    // Wait for successful login and redirect to dashboard
    await page.waitForURL('**/', { timeout: 10000 })
    await page.waitForLoadState('networkidle')
    
    // Now check for the version display in the navigation sidebar
    const sidebar = page.locator('aside')
    await expect(sidebar).toBeVisible({ timeout: 10000 })
    
    const footer = page.locator('aside footer')
    await expect(footer).toBeVisible({ timeout: 5000 })
    
    const versionText = page.locator('aside footer div')
    await expect(versionText).toBeVisible({ timeout: 5000 })
    await expect(versionText).toContainText('Version 0.1.0')
  })

  test('should display correct version format', async ({ page }) => {
    // Login
    await page.goto('/login')
    await page.fill('input[autocomplete="username"]', 'admin')
    await page.fill('input[autocomplete="current-password"]', 'TomoAdmin123!')
    await page.click('button[type="submit"]')
    
    // Wait for login
    await page.waitForURL('**/')
    await page.waitForLoadState('networkidle')
    
    // Check version text format and content
    const versionText = page.locator('aside footer div')
    await expect(versionText).toHaveText('Version 0.1.0')
    
    // Check styling classes
    await expect(versionText).toHaveClass(/text-xs/)
    await expect(versionText).toHaveClass(/text-gray-500/)
    await expect(versionText).toHaveClass(/text-center/)
  })

  test('should display version across different authenticated pages', async ({ page }) => {
    // Login
    await page.goto('/login')
    await page.fill('input[autocomplete="username"]', 'admin')
    await page.fill('input[autocomplete="current-password"]', 'TomoAdmin123!')
    await page.click('button[type="submit"]')
    
    // Wait for login
    await page.waitForURL('**/')
    await page.waitForLoadState('networkidle')
    
    const testPages = [
      { path: '/', name: 'Dashboard' },
      { path: '/servers', name: 'Servers' },
      { path: '/applications', name: 'Applications' },
      { path: '/logs', name: 'Logs' }
    ]
    
    for (const testPage of testPages) {
      await page.goto(testPage.path)
      await page.waitForLoadState('networkidle')
      
      const versionText = page.locator('aside footer div')
      await expect(versionText).toBeVisible()
      await expect(versionText).toContainText('Version 0.1.0')
    }
  })

  test('should verify footer positioning at bottom of sidebar', async ({ page }) => {
    // Login
    await page.goto('/login')
    await page.fill('input[autocomplete="username"]', 'admin')
    await page.fill('input[autocomplete="current-password"]', 'TomoAdmin123!')
    await page.click('button[type="submit"]')
    
    // Wait for login
    await page.waitForURL('**/')
    await page.waitForLoadState('networkidle')
    
    const sidebar = page.locator('aside')
    const footer = page.locator('aside footer')
    
    // Verify sidebar uses flex layout
    await expect(sidebar).toHaveClass(/flex/)
    await expect(sidebar).toHaveClass(/flex-col/)
    
    // Verify footer is at bottom with proper styling
    await expect(footer).toHaveClass(/p-4/)
    await expect(footer).toHaveClass(/border-t/)
    await expect(footer).toHaveClass(/border-gray-200/)
  })
})
