/**
 * E2E Navigation and Routing Tests
 * 
 * Comprehensive testing of navigation functionality, active states,
 * routing behavior, and UI alignment issues.
 */

import { test, expect, Page, Locator } from '@playwright/test'

// Navigation test helpers
class NavigationHelper {
  constructor(private page: Page) {}

  async login(username: string = 'admin', password: string = 'HomeLabAdmin123!'): Promise<void> {
    // Check if already authenticated by trying to go to a protected page
    await this.page.goto('/')
    const currentUrl = this.page.url()
    
    if (currentUrl.includes('/login')) {
      // Not authenticated, perform login
      await this.page.fill('input[autocomplete="username"]', username)
      await this.page.fill('input[autocomplete="current-password"]', password)
      await this.page.click('button[type="submit"]')
      
      // Wait for successful login and redirect
      await this.page.waitForURL('**/')
      await this.page.waitForLoadState('networkidle')
    }
  }

  async getNavigationItem(label: string): Promise<Locator> {
    return this.page.locator(`aside nav a:has-text("${label}")`)
  }

  async getActiveNavigationItems(): Promise<string[]> {
    const activeItems = await this.page.locator('aside nav a.nav-active').allTextContents()
    return activeItems
  }

  async waitForPageLoad(expectedPath: string): Promise<void> {
    await this.page.waitForURL(`**${expectedPath}`)
    await this.page.waitForLoadState('networkidle')
  }

  async assertNavigationHighlight(expectedActive: string): Promise<void> {
    const activeItems = await this.getActiveNavigationItems()
    expect(activeItems).toContain(expectedActive)
  }

  async assertOnlyOneActiveItem(): Promise<void> {
    const activeItems = await this.getActiveNavigationItems()
    expect(activeItems.length).toBeLessThanOrEqual(1)
  }
}

test.describe('Navigation and Routing', () => {
  let nav: NavigationHelper

  test.beforeEach(async ({ page }) => {
    nav = new NavigationHelper(page)
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
    // Login before each test to access protected routes
    await nav.login()
  })

  test.describe('Basic Navigation Structure', () => {
    test('should render all navigation items with correct structure', async ({ page }) => {
      // Verify navigation sidebar exists
      const sidebar = page.locator('aside')
      await expect(sidebar).toBeVisible()
      await expect(sidebar).toHaveClass(/w-64/)
      await expect(sidebar).toHaveClass(/min-h-screen/)

      // Check main navigation items
      const dashboardLink = await nav.getNavigationItem('Dashboard')
      const serversLink = await nav.getNavigationItem('Servers')
      const applicationsLink = await nav.getNavigationItem('Applications')
      const logsLink = await nav.getNavigationItem('Logs')

      await expect(dashboardLink).toBeVisible()
      await expect(serversLink).toBeVisible()
      await expect(applicationsLink).toBeVisible()
      await expect(logsLink).toBeVisible()

      // Check bottom navigation items
      const settingsLink = await nav.getNavigationItem('Settings')
      const helpLink = await nav.getNavigationItem('Help')

      await expect(settingsLink).toBeVisible()
      await expect(helpLink).toBeVisible()
    })

    test('should have proper navigation icons', async ({ page }) => {
      const navItems = [
        'Dashboard', 'Servers', 'Applications', 'Logs', 'Settings', 'Help'
      ]

      for (const item of navItems) {
        const link = await nav.getNavigationItem(item)
        const icon = link.locator('svg').first()
        await expect(icon).toBeVisible()
      }
    })

    test('should have correct href attributes', async ({ page }) => {
      await expect(await nav.getNavigationItem('Dashboard')).toHaveAttribute('href', '/')
      await expect(await nav.getNavigationItem('Servers')).toHaveAttribute('href', '/servers')
      await expect(await nav.getNavigationItem('Applications')).toHaveAttribute('href', '/applications')
      await expect(await nav.getNavigationItem('Logs')).toHaveAttribute('href', '/logs')
      await expect(await nav.getNavigationItem('Settings')).toHaveAttribute('href', '/settings')
      await expect(await nav.getNavigationItem('Help')).toHaveAttribute('href', '/help')
    })
  })

  test.describe('Navigation Active States', () => {
    test('should highlight Dashboard as active on home page', async ({ page }) => {
      await page.goto('/')
      await nav.waitForPageLoad('/')
      
      // Check Dashboard is active
      const dashboardLink = await nav.getNavigationItem('Dashboard')
      await expect(dashboardLink).toHaveClass(/nav-active/)
      
      // Check other items are not active
      const serversLink = await nav.getNavigationItem('Servers')
      const applicationsLink = await nav.getNavigationItem('Applications')
      
      await expect(serversLink).not.toHaveClass(/nav-active/)
      await expect(applicationsLink).not.toHaveClass(/nav-active/)
      
      // Ensure only one active item
      await nav.assertOnlyOneActiveItem()
    })

    test('should highlight Servers as active on servers page', async ({ page }) => {
      await page.goto('/servers')
      await nav.waitForPageLoad('/servers')
      
      // Check Servers is active
      const serversLink = await nav.getNavigationItem('Servers')
      await expect(serversLink).toHaveClass(/nav-active/)
      
      // Check other items are not active
      const dashboardLink = await nav.getNavigationItem('Dashboard')
      const applicationsLink = await nav.getNavigationItem('Applications')
      
      await expect(dashboardLink).not.toHaveClass(/nav-active/)
      await expect(applicationsLink).not.toHaveClass(/nav-active/)
      
      // Ensure only one active item
      await nav.assertOnlyOneActiveItem()
    })

    test('should highlight Applications as active on applications page', async ({ page }) => {
      await page.goto('/applications')
      await nav.waitForPageLoad('/applications')
      
      // Check Applications is active - THIS IS A KNOWN BUG
      const applicationsLink = await nav.getNavigationItem('Applications')
      await expect(applicationsLink).toHaveClass(/nav-active/)
      
      // Check other items are not active
      const dashboardLink = await nav.getNavigationItem('Dashboard')
      const serversLink = await nav.getNavigationItem('Servers')
      
      await expect(dashboardLink).not.toHaveClass(/nav-active/)
      await expect(serversLink).not.toHaveClass(/nav-active/)
      
      // Ensure only one active item
      await nav.assertOnlyOneActiveItem()
    })

    test('should not highlight any item for non-existent routes', async ({ page }) => {
      // Navigate to non-existent route (should redirect to dashboard)
      await page.goto('/non-existent-page')
      await nav.waitForPageLoad('/')
      
      // Should redirect to dashboard and highlight it
      const dashboardLink = await nav.getNavigationItem('Dashboard')
      await expect(dashboardLink).toHaveClass(/nav-active/)
    })
  })

  test.describe('Navigation Interaction', () => {
    test('should navigate correctly when clicking navigation items', async ({ page }) => {
      // Test Dashboard to Servers
      await page.goto('/')
      const serversLink = await nav.getNavigationItem('Servers')
      await serversLink.click()
      await nav.waitForPageLoad('/servers')
      expect(page.url()).toContain('/servers')
      await nav.assertNavigationHighlight('Servers')

      // Test Servers to Applications
      const applicationsLink = await nav.getNavigationItem('Applications')
      await applicationsLink.click()
      await nav.waitForPageLoad('/applications')
      expect(page.url()).toContain('/applications')
      await nav.assertNavigationHighlight('Applications')

      // Test Applications to Dashboard
      const dashboardLink = await nav.getNavigationItem('Dashboard')
      await dashboardLink.click()
      await nav.waitForPageLoad('/')
      expect(page.url()).not.toContain('/applications')
      await nav.assertNavigationHighlight('Dashboard')
    })

    test('should handle keyboard navigation', async ({ page }) => {
      await page.goto('/')
      
      const dashboardLink = await nav.getNavigationItem('Dashboard')
      await dashboardLink.focus()
      await expect(dashboardLink).toBeFocused()
      
      // Test Tab navigation
      await page.keyboard.press('Tab')
      const serversLink = await nav.getNavigationItem('Servers')
      await expect(serversLink).toBeFocused()
      
      // Test Enter key navigation
      await page.keyboard.press('Enter')
      await nav.waitForPageLoad('/servers')
      expect(page.url()).toContain('/servers')
    })

    test('should maintain active state during page refresh', async ({ page }) => {
      await page.goto('/applications')
      await nav.waitForPageLoad('/applications')
      
      await page.reload()
      await nav.waitForPageLoad('/applications')
      
      const applicationsLink = await nav.getNavigationItem('Applications')
      await expect(applicationsLink).toHaveClass(/nav-active/)
    })
  })

  test.describe('Navigation Accessibility', () => {
    test('should have proper ARIA attributes', async ({ page }) => {
      await page.goto('/')
      
      const sidebar = page.locator('aside')
      await expect(sidebar).toHaveAttribute('role', 'complementary')
      
      const navElements = page.locator('nav')
      await expect(navElements.first()).toHaveAttribute('role', 'navigation')
    })

    test('should support screen readers', async ({ page }) => {
      await page.goto('/')
      
      const navItems = [
        'Dashboard', 'Servers', 'Applications', 'Logs'
      ]

      for (const item of navItems) {
        const link = await nav.getNavigationItem(item)
        await expect(link).toHaveAttribute('title')
      }
    })
  })

  test.describe('Version Display', () => {
    test('should display version at bottom of sidebar', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')

      // Locate the version display in the footer
      const versionDisplay = page.locator('aside footer')
      await expect(versionDisplay).toBeVisible()

      // Check version text content
      const versionText = page.locator('aside footer div')
      await expect(versionText).toBeVisible()
      await expect(versionText).toContainText('Version 0.1.0')
    })

    test('should have correct version format and styling', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')

      // Check version text format
      const versionText = page.locator('aside footer div')
      await expect(versionText).toHaveText('Version 0.1.0')
      
      // Check styling classes
      await expect(versionText).toHaveClass(/text-xs/)
      await expect(versionText).toHaveClass(/text-gray-500/)
      await expect(versionText).toHaveClass(/text-center/)
    })

    test('should position version at bottom of sidebar', async ({ page }) => {
      await page.goto('/')
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

    test('should maintain version display across different pages', async ({ page }) => {
      const pages = ['/', '/servers', '/applications', '/logs']
      
      for (const pagePath of pages) {
        await page.goto(pagePath)
        await page.waitForLoadState('networkidle')
        
        const versionText = page.locator('aside footer div')
        await expect(versionText).toBeVisible()
        await expect(versionText).toContainText('Version 0.1.0')
      }
    })

    test('should support dark mode styling for version display', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')

      // Add dark class to body to test dark mode
      await page.addStyleTag({
        content: `body { background: #000; } .dark { display: block; }`
      })
      await page.locator('body').evaluate(el => el.classList.add('dark'))

      const versionText = page.locator('aside footer div')
      await expect(versionText).toHaveClass(/dark:text-gray-400/)
      
      const footer = page.locator('aside footer')
      await expect(footer).toHaveClass(/dark:border-gray-700/)
      
      const sidebar = page.locator('aside')
      await expect(sidebar).toHaveClass(/dark:bg-gray-900/)
    })

    test('should not break sidebar layout with version display', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')

      // Check that navigation items are still visible and properly positioned
      const navItems = ['Dashboard', 'Servers', 'Applications', 'Logs']
      
      for (const item of navItems) {
        const link = await nav.getNavigationItem(item)
        await expect(link).toBeVisible()
      }

      // Verify sidebar maintains proper width
      const sidebar = page.locator('aside')
      await expect(sidebar).toHaveClass(/w-64/)
      
      // Verify nav area is scrollable if needed
      const navArea = page.locator('aside nav')
      await expect(navArea).toHaveClass(/overflow-auto/)
      await expect(navArea).toHaveClass(/flex-1/)
    })

    test('should have version text that matches package.json', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')

      // Get version from the UI
      const versionText = await page.locator('aside footer div').textContent()
      
      // Verify it follows the expected format "Version X.Y.Z"
      expect(versionText).toMatch(/^Version \d+\.\d+\.\d+$/)
      
      // Verify it shows the correct version from package.json
      expect(versionText).toBe('Version 0.1.0')
    })
  })
})
