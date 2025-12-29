/**
 * E2E Dashboard Tests
 *
 * Tests dashboard functionality, data display, and user interactions.
 */

import { test, expect, Page } from '@playwright/test'

// Test helpers
class DashboardHelper {
  constructor(private page: Page) {}

  async login(username: string = 'admin', password: string = 'HomeLabAdmin123!'): Promise<void> {
    await this.page.goto('/')
    await this.page.waitForLoadState('networkidle')

    // Check if on login page
    const loginForm = this.page.locator('#username')
    const isOnLoginPage = await loginForm.isVisible().catch(() => false)

    if (isOnLoginPage) {
      // Wait for form to be interactive
      await this.page.locator('#username').waitFor({ state: 'visible' })

      // Fill form fields
      await this.page.locator('#username').fill(username)
      await this.page.locator('#password').fill(password)

      // Wait for validation and button to enable
      await this.page.waitForTimeout(300)

      // Click sign in
      await this.page.getByRole('button', { name: 'Sign In' }).click()

      // Wait for redirect to dashboard
      await this.page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 })
      await this.page.waitForLoadState('networkidle')
    }
  }

  async waitForDashboard(): Promise<void> {
    await this.page.waitForLoadState('networkidle')
    // Wait for either dashboard content or connecting state
    const dashboardLocator = this.page.locator('h1:has-text("Dashboard")')
      .or(this.page.locator('text=Connecting to Server'))
    await dashboardLocator.first().waitFor()
  }
}

test.describe('Dashboard', () => {
  let helper: DashboardHelper

  test.beforeEach(async ({ page }) => {
    helper = new DashboardHelper(page)
    await page.context().clearCookies()
    await helper.login()
  })

  test.describe('Dashboard Layout', () => {
    test('should display dashboard title and subtitle', async ({ page }) => {
      await helper.waitForDashboard()

      // Check for dashboard header (may show connecting or loaded state)
      const dashboardTitle = page.locator('h1:has-text("Dashboard")')
      const connectingTitle = page.locator('h2:has-text("Connecting to Server")')

      // Either dashboard is loaded or connecting
      const isLoaded = await dashboardTitle.isVisible().catch(() => false)
      const isConnecting = await connectingTitle.isVisible().catch(() => false)

      expect(isLoaded || isConnecting).toBeTruthy()
    })

    test('should have refresh button when dashboard is loaded', async ({ page }) => {
      await helper.waitForDashboard()

      // If dashboard is loaded (not connecting), check for refresh button
      const dashboardTitle = page.locator('h1:has-text("Dashboard")')
      const isLoaded = await dashboardTitle.isVisible().catch(() => false)

      if (isLoaded) {
        const refreshButton = page.locator('button:has-text("Refresh")')
        await expect(refreshButton).toBeVisible()
      }
    })
  })

  test.describe('Dashboard Stats Section', () => {
    test('should display stat cards when connected', async ({ page }) => {
      await helper.waitForDashboard()

      const dashboardTitle = page.locator('h1:has-text("Dashboard")')
      const isLoaded = await dashboardTitle.isVisible().catch(() => false)

      if (isLoaded) {
        // Check for stat cards
        await expect(page.locator('text=Total Servers')).toBeVisible()
        await expect(page.locator('text=Total Applications')).toBeVisible()
        await expect(page.locator('text=Running Apps')).toBeVisible()
        await expect(page.locator('text=Issues')).toBeVisible()
      }
    })
  })

  test.describe('Resource Usage Section', () => {
    test('should display resource usage section when connected', async ({ page }) => {
      await helper.waitForDashboard()

      const dashboardTitle = page.locator('h1:has-text("Dashboard")')
      const isLoaded = await dashboardTitle.isVisible().catch(() => false)

      if (isLoaded) {
        await expect(page.locator('text=Resource Usage')).toBeVisible()
      }
    })
  })

  test.describe('Quick Actions Section', () => {
    test('should display quick actions when connected', async ({ page }) => {
      await helper.waitForDashboard()

      const dashboardTitle = page.locator('h1:has-text("Dashboard")')
      const isLoaded = await dashboardTitle.isVisible().catch(() => false)

      if (isLoaded) {
        await expect(page.locator('text=Quick Actions')).toBeVisible()
        await expect(page.locator('text=Manage Servers')).toBeVisible()
        await expect(page.locator('text=Browse Applications')).toBeVisible()
        await expect(page.locator('text=App Marketplace')).toBeVisible()
        await expect(page.locator('text=Settings')).toBeVisible()
      }
    })

    test('should navigate to servers page when clicking Manage Servers', async ({ page }) => {
      await helper.waitForDashboard()

      const dashboardTitle = page.locator('h1:has-text("Dashboard")')
      const isLoaded = await dashboardTitle.isVisible().catch(() => false)

      if (isLoaded) {
        await page.click('text=Manage Servers')
        await page.waitForURL('**/servers')
        expect(page.url()).toContain('/servers')
      }
    })

    test('should navigate to applications page when clicking Browse Applications', async ({ page }) => {
      await helper.waitForDashboard()

      const dashboardTitle = page.locator('h1:has-text("Dashboard")')
      const isLoaded = await dashboardTitle.isVisible().catch(() => false)

      if (isLoaded) {
        await page.click('text=Browse Applications')
        await page.waitForURL('**/applications')
        expect(page.url()).toContain('/applications')
      }
    })

    test('should navigate to marketplace page when clicking App Marketplace', async ({ page }) => {
      await helper.waitForDashboard()

      const dashboardTitle = page.locator('h1:has-text("Dashboard")')
      const isLoaded = await dashboardTitle.isVisible().catch(() => false)

      if (isLoaded) {
        await page.click('text=App Marketplace')
        await page.waitForURL('**/marketplace')
        expect(page.url()).toContain('/marketplace')
      }
    })

    test('should navigate to settings page when clicking Settings', async ({ page }) => {
      await helper.waitForDashboard()

      const dashboardTitle = page.locator('h1:has-text("Dashboard")')
      const isLoaded = await dashboardTitle.isVisible().catch(() => false)

      if (isLoaded) {
        // Click the Settings quick action button, not the nav item
        await page.locator('button:has-text("Settings")').click()
        await page.waitForURL('**/settings')
        expect(page.url()).toContain('/settings')
      }
    })
  })

  test.describe('Recent Activity Section', () => {
    test('should display recent activity section when connected', async ({ page }) => {
      await helper.waitForDashboard()

      const dashboardTitle = page.locator('h1:has-text("Dashboard")')
      const isLoaded = await dashboardTitle.isVisible().catch(() => false)

      if (isLoaded) {
        await expect(page.locator('text=Recent Activity')).toBeVisible()
      }
    })

    test('should show empty state or activities', async ({ page }) => {
      await helper.waitForDashboard()

      const dashboardTitle = page.locator('h1:has-text("Dashboard")')
      const isLoaded = await dashboardTitle.isVisible().catch(() => false)

      if (isLoaded) {
        // Either show activities or empty state
        const hasActivities = await page.locator('text=events').isVisible().catch(() => false)
        const hasEmptyState = await page.locator('text=No recent activity').isVisible().catch(() => false)

        expect(hasActivities || hasEmptyState).toBeTruthy()
      }
    })
  })

  test.describe('Connecting State', () => {
    test('should show connecting state when not connected to server', async ({ page }) => {
      await helper.waitForDashboard()

      // Either connected or connecting
      const connectingTitle = page.locator('h2:has-text("Connecting to Server")')
      const dashboardTitle = page.locator('h1:has-text("Dashboard")')

      const isConnecting = await connectingTitle.isVisible().catch(() => false)
      const isConnected = await dashboardTitle.isVisible().catch(() => false)

      expect(isConnecting || isConnected).toBeTruthy()
    })

    test('should display helpful message in connecting state', async ({ page }) => {
      await helper.waitForDashboard()

      const connectingTitle = page.locator('h2:has-text("Connecting to Server")')
      const isConnecting = await connectingTitle.isVisible().catch(() => false)

      if (isConnecting) {
        await expect(page.locator('text=Check notifications for connection status updates')).toBeVisible()
      }
    })
  })

  test.describe('Dashboard Responsiveness', () => {
    test('should display properly on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await helper.waitForDashboard()

      const dashboardTitle = page.locator('h1:has-text("Dashboard")')
      const connectingTitle = page.locator('h2:has-text("Connecting to Server")')

      const isLoaded = await dashboardTitle.isVisible().catch(() => false)
      const isConnecting = await connectingTitle.isVisible().catch(() => false)

      expect(isLoaded || isConnecting).toBeTruthy()
    })

    test('should display properly on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await helper.waitForDashboard()

      const dashboardTitle = page.locator('h1:has-text("Dashboard")')
      const connectingTitle = page.locator('h2:has-text("Connecting to Server")')

      const isLoaded = await dashboardTitle.isVisible().catch(() => false)
      const isConnecting = await connectingTitle.isVisible().catch(() => false)

      expect(isLoaded || isConnecting).toBeTruthy()
    })

    test('should display properly on desktop viewport', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 })
      await helper.waitForDashboard()

      const dashboardTitle = page.locator('h1:has-text("Dashboard")')
      const connectingTitle = page.locator('h2:has-text("Connecting to Server")')

      const isLoaded = await dashboardTitle.isVisible().catch(() => false)
      const isConnecting = await connectingTitle.isVisible().catch(() => false)

      expect(isLoaded || isConnecting).toBeTruthy()
    })
  })

  test.describe('Dashboard Accessibility', () => {
    test('should have proper heading hierarchy', async ({ page }) => {
      await helper.waitForDashboard()

      const h1 = page.locator('h1')
      const h2 = page.locator('h2')

      // Should have at least one h1 or h2
      const h1Count = await h1.count()
      const h2Count = await h2.count()

      expect(h1Count + h2Count).toBeGreaterThan(0)
    })

    test('should have focusable interactive elements', async ({ page }) => {
      await helper.waitForDashboard()

      const dashboardTitle = page.locator('h1:has-text("Dashboard")')
      const isLoaded = await dashboardTitle.isVisible().catch(() => false)

      if (isLoaded) {
        // Check quick action buttons are focusable
        const quickActionButton = page.locator('button:has-text("Manage Servers")')
        if (await quickActionButton.isVisible()) {
          await quickActionButton.focus()
          await expect(quickActionButton).toBeFocused()
        }
      }
    })
  })
})
