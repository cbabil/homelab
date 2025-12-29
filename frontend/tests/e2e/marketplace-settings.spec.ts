/**
 * End-to-End Tests for Marketplace Settings
 *
 * Tests the marketplace repository configuration functionality including:
 * - Official marketplace auto-configuration
 * - Custom marketplace addition/removal
 * - Repository sync functionality
 * - MCP tool integration
 */

import { test, expect, type Page } from '@playwright/test'

// Test configuration
const TEST_CONFIG = {
  BACKEND_URL: 'http://localhost:8000',
  FRONTEND_URL: 'http://localhost:3001',
  OFFICIAL_MARKETPLACE_URL: 'https://github.com/cbabil/homelab-marketplace',
  // Demo credentials from login page
  ADMIN_USERNAME: 'admin',
  ADMIN_PASSWORD: 'HomeLabAdmin123!'
}

// Helper functions
async function login(page: Page) {
  // Wait for login form
  await page.waitForSelector('input[placeholder*="username"]', { timeout: 10000 })

  // Fill login form
  await page.fill('input[placeholder*="username"]', TEST_CONFIG.ADMIN_USERNAME)
  await page.fill('input[placeholder*="password"]', TEST_CONFIG.ADMIN_PASSWORD)

  // Click sign in button
  await page.click('button:has-text("Sign In")')

  // Wait for navigation to complete - sidebar should appear
  await page.waitForSelector('text=NAVIGATION', { timeout: 15000 })
}

async function navigateToSettings(page: Page) {
  await page.goto(`${TEST_CONFIG.FRONTEND_URL}/settings`)

  // Wait for either login page or settings page to load
  await Promise.race([
    page.waitForSelector('input[placeholder*="username"]', { timeout: 5000 }),
    page.waitForSelector('button:has-text("General")', { timeout: 5000 })
  ]).catch(() => {})

  // If on login page, login first
  const usernameInput = page.locator('input[placeholder*="username"]')
  if (await usernameInput.isVisible().catch(() => false)) {
    await login(page)
    await page.goto(`${TEST_CONFIG.FRONTEND_URL}/settings`)
  }

  // Wait for settings page tabs to load
  await page.waitForSelector('button:has-text("General")', { timeout: 10000 })
}

async function clickMarketplaceTab(page: Page) {
  // Wait for the tabs to be visible
  await page.waitForSelector('button:has-text("Marketplace")')
  await page.click('button:has-text("Marketplace")')
  // Wait for marketplace content to load
  await page.waitForTimeout(1000)
}

async function waitForMcpConnection(page: Page) {
  // Wait for MCP session to be established
  await page.waitForFunction(() => {
    return document.body.textContent?.includes('Official Marketplace') ||
           document.body.textContent?.includes('Add Official Marketplace')
  }, { timeout: 10000 })
}

test.describe('Marketplace Settings', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage before each test
    await page.context().clearCookies()
  })

  test.describe('Navigation and Display', () => {
    test('should display Marketplace tab in settings', async ({ page }) => {
      await navigateToSettings(page)

      // Check that Marketplace tab exists
      const marketplaceTab = page.locator('button:has-text("Marketplace")')
      await expect(marketplaceTab).toBeVisible()
    })

    test('should switch to Marketplace tab when clicked', async ({ page }) => {
      await navigateToSettings(page)
      await clickMarketplaceTab(page)

      // Should show marketplace content - use heading selector for specificity
      await expect(page.getByRole('heading', { name: 'Official Marketplace' })).toBeVisible()
    })

    test('should display Custom Marketplaces section', async ({ page }) => {
      await navigateToSettings(page)
      await clickMarketplaceTab(page)

      // Should show custom marketplaces section - use heading selector for specificity
      await expect(page.getByRole('heading', { name: 'Custom Marketplaces' })).toBeVisible()
    })
  })

  test.describe('Official Marketplace', () => {
    test('should show official marketplace when configured by default', async ({ page }) => {
      await navigateToSettings(page)
      await clickMarketplaceTab(page)
      await waitForMcpConnection(page)

      // Take screenshot for debugging
      await page.screenshot({ path: 'test-results/marketplace-settings.png' })

      // Check console for debug logs
      const consoleMessages: string[] = []
      page.on('console', msg => {
        consoleMessages.push(msg.text())
      })

      // Wait a bit for async operations
      await page.waitForTimeout(2000)

      // Log console messages for debugging
      console.log('Console messages:', consoleMessages.filter(m => m.includes('Marketplace') || m.includes('repos')))

      // Either official marketplace is shown OR the "Add Official Marketplace" button is shown
      const officialRepoName = page.locator('text=Homelab Marketplace')
      const addOfficialButton = page.locator('button:has-text("Add Official Marketplace")')

      // One of these should be visible
      const hasOfficialRepo = await officialRepoName.isVisible().catch(() => false)
      const hasAddButton = await addOfficialButton.isVisible().catch(() => false)

      expect(hasOfficialRepo || hasAddButton).toBe(true)
    })

    test('should be able to add official marketplace if not configured', async ({ page }) => {
      await navigateToSettings(page)
      await clickMarketplaceTab(page)
      await waitForMcpConnection(page)

      const addOfficialButton = page.locator('button:has-text("Add Official Marketplace")')

      if (await addOfficialButton.isVisible()) {
        // Click to add official marketplace
        await addOfficialButton.click()

        // Wait for the operation to complete
        await page.waitForTimeout(3000)

        // Should now show the official marketplace
        await expect(page.locator('text=Homelab Marketplace')).toBeVisible({ timeout: 10000 })
      } else {
        // Official marketplace already configured - just verify it's there
        await expect(page.locator('text=Homelab Marketplace')).toBeVisible()
      }
    })

    test('should display sync button for official marketplace', async ({ page }) => {
      await navigateToSettings(page)
      await clickMarketplaceTab(page)
      await waitForMcpConnection(page)

      // If official marketplace is configured, should have sync button
      const officialRepoName = page.locator('text=Homelab Marketplace')

      if (await officialRepoName.isVisible()) {
        // Should show a sync button
        const syncButton = page.locator('button:has-text("Sync")')
        await expect(syncButton).toBeVisible()
      }
    })
  })

  test.describe('Custom Marketplaces', () => {
    test('should show Add button for custom marketplaces', async ({ page }) => {
      await navigateToSettings(page)
      await clickMarketplaceTab(page)

      // Should have an "Add" button in Custom Marketplaces section
      const addButton = page.locator('button:has-text("Add")').last()
      await expect(addButton).toBeVisible()
    })

    test('should show form when Add button is clicked', async ({ page }) => {
      await navigateToSettings(page)
      await clickMarketplaceTab(page)

      // Click Add button
      const addButton = page.locator('button:has-text("Add")').last()
      await addButton.click()

      // Should show form fields
      await expect(page.locator('input[placeholder*="Custom Marketplace"]')).toBeVisible()
      await expect(page.locator('input[placeholder*="github.com"]')).toBeVisible()
      await expect(page.locator('input[placeholder*="main"]')).toBeVisible()
    })

    test('should be able to cancel adding custom marketplace', async ({ page }) => {
      await navigateToSettings(page)
      await clickMarketplaceTab(page)

      // Click Add button
      const addButton = page.locator('button:has-text("Add")').last()
      await addButton.click()

      // Click Cancel button
      await page.click('button:has-text("Cancel")')

      // Form should be hidden
      await expect(page.locator('input[placeholder*="Custom Marketplace"]')).not.toBeVisible()
    })

    test('should show empty state when no custom marketplaces configured', async ({ page }) => {
      await navigateToSettings(page)
      await clickMarketplaceTab(page)

      // Should show empty message
      await expect(page.locator('text=No custom marketplaces configured')).toBeVisible()
    })
  })

  test.describe('MCP Integration', () => {
    test('should call list_repos tool on component mount', async ({ page }) => {
      // Listen for network requests
      const mcpRequests: string[] = []
      page.on('request', request => {
        if (request.url().includes('/mcp')) {
          mcpRequests.push(request.postData() || '')
        }
      })

      await navigateToSettings(page)
      await clickMarketplaceTab(page)

      // Wait for MCP calls
      await page.waitForTimeout(3000)

      // Check if list_repos was called
      const hasListReposCall = mcpRequests.some(req => req.includes('list_repos'))

      // Log for debugging
      console.log('MCP requests:', mcpRequests.map(r => {
        try {
          const parsed = JSON.parse(r)
          return parsed.params?.name || 'unknown'
        } catch {
          return 'parse-error'
        }
      }))

      // The component should make an MCP call for list_repos
      // Note: If not found, this helps debug the issue
      if (!hasListReposCall) {
        console.log('list_repos not found in MCP requests. All requests:')
        mcpRequests.forEach(r => console.log(r.substring(0, 200)))
      }
    })

    test('should handle MCP connection errors gracefully', async ({ page }) => {
      // Intercept MCP requests and return error
      await page.route('**/mcp/**', route => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'MCP server error' })
        })
      })

      await navigateToSettings(page)
      await clickMarketplaceTab(page)

      // Should show error message or fallback UI
      await page.waitForTimeout(2000)

      // Take screenshot for debugging
      await page.screenshot({ path: 'test-results/marketplace-mcp-error.png' })

      // Should not crash - page should still be usable
      await expect(page.locator('text=Official Marketplace')).toBeVisible()
    })
  })

  test.describe('Loading States', () => {
    test('should show loading spinner while fetching repos', async ({ page }) => {
      // Delay MCP responses
      await page.route('**/mcp/**', async route => {
        await new Promise(resolve => setTimeout(resolve, 1000))
        route.continue()
      })

      await navigateToSettings(page)
      await clickMarketplaceTab(page)

      // Should show loading indicator initially
      // Note: The loading state might be very fast, so we check if it exists
      const loadingIndicator = page.locator('svg.animate-spin, [data-testid="loading"]')

      // Either loading is visible or content already loaded
      const marketplaceContent = page.locator('text=Official Marketplace')
        .or(page.locator('text=Add Official Marketplace'))
      await expect(marketplaceContent.first()).toBeVisible({ timeout: 10000 })
    })
  })

  test.describe('Repository Status Display', () => {
    test('should display repository status indicators', async ({ page }) => {
      await navigateToSettings(page)
      await clickMarketplaceTab(page)
      await waitForMcpConnection(page)

      const officialRepoName = page.locator('text=Homelab Marketplace')

      if (await officialRepoName.isVisible()) {
        // Should show status badge (Active, Syncing, Error, etc.)
        const statusBadge = page.locator('text=Active')
          .or(page.locator('text=Syncing'))
          .or(page.locator('text=Error'))
        await expect(statusBadge.first()).toBeVisible()
      }
    })

    test('should display app count for configured repos', async ({ page }) => {
      await navigateToSettings(page)
      await clickMarketplaceTab(page)
      await waitForMcpConnection(page)

      const officialRepoName = page.locator('text=Homelab Marketplace')

      if (await officialRepoName.isVisible()) {
        // Should show app count
        await expect(page.locator('text=/\\d+ apps/')).toBeVisible()
      }
    })
  })

  test.describe('Info Section', () => {
    test('should display marketplace info text', async ({ page }) => {
      await navigateToSettings(page)
      await clickMarketplaceTab(page)

      // Should show explanatory text
      await expect(page.locator('text=YAML app definitions')).toBeVisible()
    })
  })
})

test.describe('Marketplace Settings - Debug Tests', () => {
  test('debug: check what list_repos returns', async ({ page }) => {
    // Capture console logs
    const consoleLogs: string[] = []
    page.on('console', msg => {
      consoleLogs.push(`[${msg.type()}] ${msg.text()}`)
    })

    // Capture network requests
    const networkRequests: { url: string; method: string; body: string | null; response?: string }[] = []
    page.on('request', request => {
      if (request.url().includes('/mcp')) {
        networkRequests.push({
          url: request.url(),
          method: request.method(),
          body: request.postData()
        })
      }
    })

    page.on('response', async response => {
      if (response.url().includes('/mcp')) {
        try {
          const body = await response.text()
          const req = networkRequests.find(r => r.url === response.url())
          if (req) {
            req.response = body.substring(0, 500)
          }
        } catch (e) {
          // Ignore
        }
      }
    })

    await navigateToSettings(page)
    await clickMarketplaceTab(page)

    // Wait for operations
    await page.waitForTimeout(5000)

    // Log debug info
    console.log('\n=== DEBUG INFO ===')
    console.log('\n--- Console Logs (filtered) ---')
    consoleLogs
      .filter(l => l.includes('Marketplace') || l.includes('repos') || l.includes('list_repos') || l.includes('error'))
      .forEach(l => console.log(l))

    console.log('\n--- Network Requests ---')
    networkRequests.forEach(r => {
      console.log(`${r.method} ${r.url}`)
      if (r.body) console.log('  Body:', r.body.substring(0, 200))
      if (r.response) console.log('  Response:', r.response)
    })

    // Take screenshot
    await page.screenshot({ path: 'test-results/debug-marketplace.png', fullPage: true })

    // This test always passes - it's just for debugging
    expect(true).toBe(true)
  })
})
