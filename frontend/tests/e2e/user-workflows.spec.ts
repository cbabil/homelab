/**
 * Complete User Workflow Integration Tests
 * 
 * End-to-end testing of complete user journeys through the application,
 * including navigation flows, search functionality, and UI interactions.
 */

import { test, expect, Page } from '@playwright/test'

class UserWorkflowHelper {
  constructor(private page: Page) {}

  async navigateToPage(pageName: string, expectedPath: string): Promise<void> {
    const navLink = this.page.locator(`aside nav a:has-text("${pageName}")`)
    await navLink.click()
    await this.page.waitForURL(`**${expectedPath}`)
    await this.page.waitForLoadState('networkidle')
  }

  async verifyPageLoaded(pageTitle: string): Promise<void> {
    const title = this.page.locator(`h1:text("${pageTitle}")`)
    await expect(title).toBeVisible()
  }

  async verifyActiveNavigation(expectedActive: string): Promise<void> {
    const activeLink = this.page.locator(`aside nav a:has-text("${expectedActive}").nav-active`)
    await expect(activeLink).toBeVisible()
  }

  async performSearch(searchTerm: string): Promise<void> {
    const searchInput = this.page.locator('input[placeholder*="Search"]')
    await searchInput.fill(searchTerm)
    await this.page.waitForTimeout(500) // Wait for search debounce
  }

  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({ 
      path: `tests/screenshots/${name}.png`, 
      fullPage: true 
    })
  }
}

test.describe('Complete User Workflows', () => {
  let workflow: UserWorkflowHelper

  test.beforeEach(async ({ page }) => {
    workflow = new UserWorkflowHelper(page)
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test.describe('Navigation Flow Testing', () => {
    test('complete navigation tour through all pages', async ({ page }) => {
      // Start at Dashboard
      await workflow.verifyPageLoaded('Dashboard')
      await workflow.verifyActiveNavigation('Dashboard')
      await workflow.takeScreenshot('01-dashboard-initial')

      // Navigate to Servers
      await workflow.navigateToPage('Servers', '/servers')
      await workflow.verifyPageLoaded('Server Management')
      await workflow.verifyActiveNavigation('Servers')
      await workflow.takeScreenshot('02-servers-page')

      // Navigate to Applications
      await workflow.navigateToPage('Applications', '/applications')
      await workflow.verifyPageLoaded('Application Marketplace')
      await workflow.verifyActiveNavigation('Applications')
      await workflow.takeScreenshot('03-applications-page')

      // Navigate to Logs
      await workflow.navigateToPage('Logs', '/logs')
      await workflow.verifyPageLoaded('Logs')
      await workflow.verifyActiveNavigation('Logs')
      await workflow.takeScreenshot('04-logs-page')

      // Navigate back to Dashboard
      await workflow.navigateToPage('Dashboard', '/')
      await workflow.verifyPageLoaded('Dashboard')
      await workflow.verifyActiveNavigation('Dashboard')
      await workflow.takeScreenshot('05-back-to-dashboard')
    })

    test('navigation state persistence across page refreshes', async ({ page }) => {
      // Navigate to Applications
      await workflow.navigateToPage('Applications', '/applications')
      await workflow.verifyActiveNavigation('Applications')

      // Refresh page
      await page.reload()
      await page.waitForLoadState('networkidle')

      // Verify state is maintained
      await workflow.verifyPageLoaded('Application Marketplace')
      await workflow.verifyActiveNavigation('Applications')
    })

    test('browser back and forward navigation', async ({ page }) => {
      // Navigate through pages
      await workflow.navigateToPage('Applications', '/applications')
      await workflow.verifyActiveNavigation('Applications')

      await workflow.navigateToPage('Servers', '/servers')
      await workflow.verifyActiveNavigation('Servers')

      // Use browser back button
      await page.goBack()
      await page.waitForLoadState('networkidle')
      await workflow.verifyActiveNavigation('Applications')

      // Use browser forward button
      await page.goForward()
      await page.waitForLoadState('networkidle')
      await workflow.verifyActiveNavigation('Servers')
    })
  })

  test.describe('Applications Page User Journey', () => {
    test('complete application discovery and management flow', async ({ page }) => {
      // Navigate to Applications
      await workflow.navigateToPage('Applications', '/applications')
      await workflow.verifyPageLoaded('Application Marketplace')
      await workflow.takeScreenshot('apps-01-marketplace-landing')

      // Test category filtering
      const mediaCategory = page.locator('button:has(p:text("Media Server"))')
      if (await mediaCategory.count() > 0) {
        await mediaCategory.click()
        await page.waitForTimeout(500)
        await expect(mediaCategory).toHaveClass(/border-primary/)
        await workflow.takeScreenshot('apps-02-media-category-filter')
      }

      // Reset to all apps
      const allAppsButton = page.locator('button:has(p:text("All Apps"))')
      await allAppsButton.click()
      await page.waitForTimeout(500)
      await workflow.takeScreenshot('apps-03-all-apps-reset')

      // Test search functionality
      await workflow.performSearch('Plex')
      await workflow.takeScreenshot('apps-04-search-results')

      // Clear search and verify reset
      const searchInput = page.locator('input[placeholder*="Search applications"]')
      await searchInput.clear()
      await page.waitForTimeout(500)
      await workflow.takeScreenshot('apps-05-search-cleared')

      // Test application card interactions
      const firstCard = page.locator('.bg-card.p-6.rounded-xl.border').first()
      await firstCard.hover()
      await page.waitForTimeout(300) // Wait for hover animation
      await workflow.takeScreenshot('apps-06-card-hover')

      // Test install button interaction
      const installButton = firstCard.locator('button').last()
      if (await installButton.count() > 0) {
        const buttonText = await installButton.textContent()
        if (buttonText?.includes('Install')) {
          await installButton.hover()
          await workflow.takeScreenshot('apps-07-install-button-hover')
        }
      }
    })

    test('responsive design user journey', async ({ page }) => {
      await workflow.navigateToPage('Applications', '/applications')

      // Test desktop layout
      await page.setViewportSize({ width: 1920, height: 1080 })
      await page.waitForLoadState('networkidle')
      await workflow.takeScreenshot('responsive-01-desktop-1920')

      // Test laptop layout
      await page.setViewportSize({ width: 1366, height: 768 })
      await page.waitForLoadState('networkidle')
      await workflow.takeScreenshot('responsive-02-laptop-1366')

      // Test tablet layout
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.waitForLoadState('networkidle')
      await workflow.takeScreenshot('responsive-03-tablet-768')

      // Test mobile layout
      await page.setViewportSize({ width: 375, height: 812 })
      await page.waitForLoadState('networkidle')
      await workflow.takeScreenshot('responsive-04-mobile-375')

      // Verify navigation is still accessible on mobile
      const sidebar = page.locator('aside')
      await expect(sidebar).toBeVisible()

      // Test mobile navigation interaction
      const applicationsLink = page.locator('aside nav a:has-text("Applications")')
      await expect(applicationsLink).toBeVisible()
      await workflow.takeScreenshot('responsive-05-mobile-nav')
    })
  })

  test.describe('Error Handling and Edge Cases', () => {
    test('handle missing pages gracefully', async ({ page }) => {
      // Test non-existent route
      await page.goto('/non-existent-page')
      await page.waitForLoadState('networkidle')
      
      // Should redirect to dashboard or show proper error
      const url = page.url()
      expect(url).toMatch(/\/(dashboard)?$/)
      await workflow.takeScreenshot('error-01-non-existent-route')
    })

    test('handle slow network conditions', async ({ page }) => {
      // Simulate slow 3G connection
      await page.route('**/*', (route) => {
        setTimeout(() => route.continue(), 100) // Add 100ms delay
      })

      await workflow.navigateToPage('Applications', '/applications')
      await workflow.verifyPageLoaded('Application Marketplace')
      await workflow.takeScreenshot('error-02-slow-network')
    })

    test('handle search with no results', async ({ page }) => {
      await workflow.navigateToPage('Applications', '/applications')
      
      // Search for something that doesn't exist
      await workflow.performSearch('NonExistentApplication123')
      
      // Verify empty state
      const emptyState = page.locator(':text("No applications found")')
      await expect(emptyState).toBeVisible()
      await workflow.takeScreenshot('error-03-no-search-results')
    })
  })

  test.describe('Accessibility and Keyboard Navigation', () => {
    test('complete keyboard navigation workflow', async ({ page }) => {
      await page.goto('/')
      
      // Test tab navigation through main navigation
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab')
      
      // Navigate to applications using keyboard
      const applicationsLink = page.locator('aside nav a:has-text("Applications")')
      await applicationsLink.focus()
      await page.keyboard.press('Enter')
      
      await workflow.verifyPageLoaded('Application Marketplace')
      await workflow.verifyActiveNavigation('Applications')
      await workflow.takeScreenshot('accessibility-01-keyboard-nav')

      // Test keyboard navigation within applications page
      const searchInput = page.locator('input[placeholder*="Search applications"]')
      await searchInput.focus()
      await searchInput.type('test')
      await workflow.takeScreenshot('accessibility-02-keyboard-search')
    })

    test('screen reader compatibility', async ({ page }) => {
      await workflow.navigateToPage('Applications', '/applications')
      
      // Check for proper ARIA labels and roles
      const sidebar = page.locator('aside')
      await expect(sidebar).toHaveAttribute('role', 'complementary')
      
      const navElement = page.locator('nav').first()
      await expect(navElement).toHaveAttribute('role', 'navigation')
      
      // Check navigation items have proper accessibility
      const navItems = page.locator('aside nav a')
      const navItemsCount = await navItems.count()
      
      for (let i = 0; i < navItemsCount; i++) {
        const navItem = navItems.nth(i)
        await expect(navItem).toHaveAttribute('title')
      }
    })
  })

  test.describe('Performance and Loading', () => {
    test('measure page load performance', async ({ page }) => {
      // Measure navigation timing
      const startTime = Date.now()
      
      await workflow.navigateToPage('Applications', '/applications')
      
      const endTime = Date.now()
      const loadTime = endTime - startTime
      
      // Should load within 3 seconds
      expect(loadTime).toBeLessThan(3000)
      
      // Verify all key elements loaded
      await expect(page.locator('h1:text("Application Marketplace")')).toBeVisible()
      await expect(page.locator('.bg-card.p-6.rounded-xl.border').first()).toBeVisible()
    })

    test('verify animations and transitions work smoothly', async ({ page }) => {
      await workflow.navigateToPage('Applications', '/applications')
      
      // Test card hover animations
      const firstCard = page.locator('.bg-card.p-6.rounded-xl.border').first()
      
      // Hover and wait for animation
      await firstCard.hover()
      await page.waitForTimeout(300)
      
      // Move away and hover again
      await page.mouse.move(0, 0)
      await page.waitForTimeout(300)
      await firstCard.hover()
      await page.waitForTimeout(300)
      
      await workflow.takeScreenshot('performance-01-smooth-animations')
    })
  })
})
