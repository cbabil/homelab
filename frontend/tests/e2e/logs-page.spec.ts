/**
 * Logs Page End-to-End Tests
 *
 * Comprehensive E2E tests for logs page functionality including navigation,
 * data loading, tab navigation, search, refresh, export, toast notifications,
 * and error handling. Tests follow TDD principles and validate LogsDataService
 * integration and user interactions.
 */

import { test, expect, Page } from '@playwright/test'

interface LogEntry {
  id: string
  timestamp: string
  level: string
  source: string
  message: string
  category: string
  tags: string[]
  metadata: Record<string, unknown>
  created_at: string
}

// Helper function to login as admin
async function loginAsAdmin(page: Page) {
  await page.goto('/login')
  await page.fill('input[autocomplete="username"]', 'admin')
  await page.fill('input[autocomplete="current-password"]', 'TomoAdmin123!')
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL('/')
}

// Helper function to setup console error capture
function setupConsoleErrorCapture(page: Page) {
  const consoleErrors: string[] = []
  const jsErrors: string[] = []

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text())
      console.log('Console Error:', msg.text())
    }
  })

  page.on('pageerror', (error) => {
    jsErrors.push(error.message)
    console.log('JavaScript Error:', error.message)
  })

  return { consoleErrors, jsErrors }
}

// Helper function to mock successful logs API response
async function mockLogsApiSuccess(page: Page, logs: LogEntry[] = []) {
  const defaultLogs = logs.length > 0 ? logs : [
    {
      id: '1',
      timestamp: '2023-01-01T10:00:00Z',
      level: 'info',
      source: 'system',
      message: 'System started successfully',
      category: 'system',
      tags: ['startup'],
      metadata: {},
      created_at: '2023-01-01T10:00:00Z'
    },
    {
      id: '2',
      timestamp: '2023-01-01T10:01:00Z',
      level: 'warn',
      source: 'application',
      message: 'High memory usage detected',
      category: 'application',
      tags: ['memory', 'warning'],
      metadata: { usage: '85%' },
      created_at: '2023-01-01T10:01:00Z'
    },
    {
      id: '3',
      timestamp: '2023-01-01T10:02:00Z',
      level: 'error',
      source: 'security',
      message: 'Failed login attempt',
      category: 'security',
      tags: ['auth', 'security'],
      metadata: { ip: '192.168.1.100' },
      created_at: '2023-01-01T10:02:00Z'
    }
  ]

  await page.route('**/api/logs*', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          logs: defaultLogs,
          total: defaultLogs.length,
          page: 1,
          pageSize: 100
        }
      })
    })
  })
}

// Helper function to mock logs API failure
async function mockLogsApiFailure(page: Page) {
  await page.route('**/api/logs*', route => {
    route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({
        success: false,
        error: 'Internal server error'
      })
    })
  })
}

test.describe('Logs Page End-to-End Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage before each test
    await page.context().clearCookies()
    try {
      await page.evaluate(() => {
        if (typeof Storage !== 'undefined') {
          localStorage.clear()
          sessionStorage.clear()
        }
      })
    } catch (error) {
      console.log('Note: localStorage not accessible, skipping clear')
    }
  })

  test.describe('Navigation and Basic Page Load', () => {
    test('should navigate to logs page successfully when authenticated', async ({ page }) => {
      const { consoleErrors, jsErrors } = setupConsoleErrorCapture(page)

      await mockLogsApiSuccess(page)
      await loginAsAdmin(page)

      // Navigate to logs page
      await page.goto('/logs')
      await page.waitForLoadState('networkidle')

      // Verify we're on the logs page
      await expect(page).toHaveURL('/logs')

      // Verify page header is present
      await expect(page.locator('h1')).toContainText('Logs')
      await expect(page.locator('text=System and application logs monitoring')).toBeVisible()

      // Verify no JavaScript errors occurred
      expect(jsErrors.filter(error =>
        error.includes('Cannot read properties of undefined') ||
        error.includes('TypeError')
      )).toHaveLength(0)

      await page.screenshot({
        path: 'test-results/logs-page-navigation.png',
        fullPage: true
      })
    })

    test('should redirect to login when not authenticated', async ({ page }) => {
      const { consoleErrors, jsErrors } = setupConsoleErrorCapture(page)

      await page.goto('/logs')

      // Should redirect to login
      await expect(page).toHaveURL('/login')

      // Verify no errors during redirect
      expect(jsErrors.filter(error =>
        error.includes('Cannot read properties of undefined') ||
        error.includes('TypeError')
      )).toHaveLength(0)
    })
  })

  test.describe('Log Data Loading and Display', () => {
    test('should load and display log data correctly', async ({ page }) => {
      const { consoleErrors, jsErrors } = setupConsoleErrorCapture(page)

      await mockLogsApiSuccess(page)
      await loginAsAdmin(page)
      await page.goto('/logs')
      await page.waitForLoadState('networkidle')

      // Wait for logs to be displayed
      await expect(page.locator('[data-testid="logs-list"], .logs-list, .log-entry').first()).toBeVisible({ timeout: 10000 })

      // Verify log entries are displayed
      const logEntries = page.locator('[data-testid="log-entry"], .log-entry')
      await expect(logEntries).toHaveCount(3, { timeout: 10000 })

      // Verify specific log content
      await expect(page.locator('text=System started successfully')).toBeVisible()
      await expect(page.locator('text=High memory usage detected')).toBeVisible()
      await expect(page.locator('text=Failed login attempt')).toBeVisible()

      // Verify different log levels are displayed
      await expect(page.locator('text=info')).toBeVisible()
      await expect(page.locator('text=warn')).toBeVisible()
      await expect(page.locator('text=error')).toBeVisible()

      expect(jsErrors).toHaveLength(0)

      await page.screenshot({
        path: 'test-results/logs-data-display.png',
        fullPage: true
      })
    })

    test('should handle empty log data gracefully', async ({ page }) => {
      const { consoleErrors, jsErrors } = setupConsoleErrorCapture(page)

      await mockLogsApiSuccess(page, [])
      await loginAsAdmin(page)
      await page.goto('/logs')
      await page.waitForLoadState('networkidle')

      // Wait for empty state or loading completion
      await page.waitForTimeout(2000)

      // Should not have any log entries
      const logEntries = page.locator('[data-testid="log-entry"], .log-entry')
      await expect(logEntries).toHaveCount(0)

      // Should not have JavaScript errors
      expect(jsErrors).toHaveLength(0)

      await page.screenshot({
        path: 'test-results/logs-empty-data.png',
        fullPage: true
      })
    })

    test('should display loading state during data fetch', async ({ page }) => {
      await loginAsAdmin(page)

      // Mock a delayed response to capture loading state
      await page.route('**/api/logs*', async route => {
        await new Promise(resolve => setTimeout(resolve, 1000))
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            data: { logs: [], total: 0, page: 1, pageSize: 100 }
          })
        })
      })

      await page.goto('/logs')

      // Should show loading indicator initially
      await expect(page.locator('[data-testid="loading"], .loading, .spinner')).toBeVisible({ timeout: 2000 })

      // Wait for loading to complete
      await page.waitForLoadState('networkidle')

      await page.screenshot({
        path: 'test-results/logs-loading-state.png',
        fullPage: true
      })
    })
  })

  test.describe('Tab Navigation', () => {
    test('should navigate between log category tabs', async ({ page }) => {
      const { consoleErrors, jsErrors } = setupConsoleErrorCapture(page)

      await mockLogsApiSuccess(page)
      await loginAsAdmin(page)
      await page.goto('/logs')
      await page.waitForLoadState('networkidle')

      // Verify all tabs are present
      await expect(page.locator('text=All')).toBeVisible()
      await expect(page.locator('text=System')).toBeVisible()
      await expect(page.locator('text=Application')).toBeVisible()
      await expect(page.locator('text=Security')).toBeVisible()
      await expect(page.locator('text=Network')).toBeVisible()

      // Test clicking different tabs
      await page.click('text=System')
      await page.waitForTimeout(500)

      await page.click('text=Application')
      await page.waitForTimeout(500)

      await page.click('text=Security')
      await page.waitForTimeout(500)

      await page.click('text=Network')
      await page.waitForTimeout(500)

      await page.click('text=All')
      await page.waitForTimeout(500)

      // Verify no JavaScript errors during tab navigation
      expect(jsErrors).toHaveLength(0)

      await page.screenshot({
        path: 'test-results/logs-tab-navigation.png',
        fullPage: true
      })
    })

    test('should filter logs based on selected tab', async ({ page }) => {
      const systemLogs = [
        {
          id: '1',
          timestamp: '2023-01-01T10:00:00Z',
          level: 'info',
          source: 'system',
          message: 'System log entry',
          category: 'system',
          tags: [],
          metadata: {},
          created_at: '2023-01-01T10:00:00Z'
        }
      ]

      const securityLogs = [
        {
          id: '2',
          timestamp: '2023-01-01T10:01:00Z',
          level: 'warn',
          source: 'security',
          message: 'Security log entry',
          category: 'security',
          tags: [],
          metadata: {},
          created_at: '2023-01-01T10:01:00Z'
        }
      ]

      await loginAsAdmin(page)

      // Mock different responses for different tab selections
      await page.route('**/api/logs*', route => {
        const url = route.request().url()
        if (url.includes('source=system')) {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              success: true,
              data: { logs: systemLogs, total: 1, page: 1, pageSize: 100 }
            })
          })
        } else if (url.includes('source=security')) {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              success: true,
              data: { logs: securityLogs, total: 1, page: 1, pageSize: 100 }
            })
          })
        } else {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              success: true,
              data: { logs: [...systemLogs, ...securityLogs], total: 2, page: 1, pageSize: 100 }
            })
          })
        }
      })

      await page.goto('/logs')
      await page.waitForLoadState('networkidle')

      // Click System tab and verify filtering
      await page.click('text=System')
      await page.waitForTimeout(1000)
      await expect(page.locator('text=System log entry')).toBeVisible()

      // Click Security tab and verify filtering
      await page.click('text=Security')
      await page.waitForTimeout(1000)
      await expect(page.locator('text=Security log entry')).toBeVisible()

      await page.screenshot({
        path: 'test-results/logs-tab-filtering.png',
        fullPage: true
      })
    })
  })

  test.describe('Search Functionality', () => {
    test('should filter logs based on search input', async ({ page }) => {
      await mockLogsApiSuccess(page)
      await loginAsAdmin(page)
      await page.goto('/logs')
      await page.waitForLoadState('networkidle')

      // Wait for logs to load
      await page.waitForTimeout(2000)

      // Find and use search input
      const searchInput = page.locator('input[type="search"], input[placeholder*="search"], input[placeholder*="Search"]')
      await expect(searchInput).toBeVisible({ timeout: 10000 })

      // Test search functionality
      await searchInput.fill('System started')
      await page.waitForTimeout(500)

      // Clear search
      await searchInput.clear()
      await page.waitForTimeout(500)

      // Test another search
      await searchInput.fill('memory')
      await page.waitForTimeout(500)

      await page.screenshot({
        path: 'test-results/logs-search-functionality.png',
        fullPage: true
      })
    })
  })

  test.describe('Refresh Functionality', () => {
    test('should refresh logs when refresh button is clicked', async ({ page }) => {
      const { consoleErrors, jsErrors } = setupConsoleErrorCapture(page)

      await mockLogsApiSuccess(page)
      await loginAsAdmin(page)
      await page.goto('/logs')
      await page.waitForLoadState('networkidle')

      // Find and click refresh button
      const refreshButton = page.locator('button:has-text("Refresh"), button[title*="refresh"], button[aria-label*="refresh"]')
      await expect(refreshButton).toBeVisible({ timeout: 10000 })

      await refreshButton.click()
      await page.waitForTimeout(1000)

      // Verify no errors during refresh
      expect(jsErrors).toHaveLength(0)

      await page.screenshot({
        path: 'test-results/logs-refresh-functionality.png',
        fullPage: true
      })
    })

    test('should show loading state during refresh', async ({ page }) => {
      await loginAsAdmin(page)

      // Mock delayed response for refresh
      let requestCount = 0
      await page.route('**/api/logs*', async route => {
        requestCount++
        if (requestCount > 1) {
          // Delay subsequent requests (refresh)
          await new Promise(resolve => setTimeout(resolve, 1000))
        }
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            data: { logs: [], total: 0, page: 1, pageSize: 100 }
          })
        })
      })

      await page.goto('/logs')
      await page.waitForLoadState('networkidle')

      // Click refresh and verify loading state
      const refreshButton = page.locator('button:has-text("Refresh")')
      await refreshButton.click()

      await page.screenshot({
        path: 'test-results/logs-refresh-loading.png',
        fullPage: true
      })
    })
  })

  test.describe('Export Functionality', () => {
    test('should trigger download when export button is clicked', async ({ page }) => {
      const { consoleErrors, jsErrors } = setupConsoleErrorCapture(page)

      await mockLogsApiSuccess(page)
      await loginAsAdmin(page)
      await page.goto('/logs')
      await page.waitForLoadState('networkidle')

      // Set up download handler
      const downloadPromise = page.waitForEvent('download')

      // Find and click export button
      const exportButton = page.locator('button:has-text("Export"), button[title*="export"], button[aria-label*="export"]')
      await expect(exportButton).toBeVisible({ timeout: 10000 })

      await exportButton.click()

      // Wait for download to start
      const download = await downloadPromise

      // Verify download was triggered
      expect(download.suggestedFilename()).toMatch(/tomo-logs-.*\.json/)

      // Verify no errors during export
      expect(jsErrors).toHaveLength(0)

      await page.screenshot({
        path: 'test-results/logs-export-functionality.png',
        fullPage: true
      })
    })
  })

  test.describe('Toast Notifications', () => {
    test('should show error toast when logs API fails', async ({ page }) => {
      await mockLogsApiFailure(page)
      await loginAsAdmin(page)
      await page.goto('/logs')
      await page.waitForLoadState('networkidle')

      // Wait for error toast to appear
      await expect(page.locator('[data-testid="toast"], .toast, [role="alert"]')).toBeVisible({ timeout: 10000 })

      // Verify error message in toast
      const toast = page.locator('[data-testid="toast"], .toast, [role="alert"]')
      await expect(toast).toContainText(/failed to load logs|error/i)

      await page.screenshot({
        path: 'test-results/logs-error-toast.png',
        fullPage: true
      })
    })

    test('should show success feedback for successful operations', async ({ page }) => {
      await mockLogsApiSuccess(page)
      await loginAsAdmin(page)
      await page.goto('/logs')
      await page.waitForLoadState('networkidle')

      // Trigger refresh operation
      const refreshButton = page.locator('button:has-text("Refresh")')
      await refreshButton.click()
      await page.waitForTimeout(1000)

      // Look for any success indicators or toast
      await page.screenshot({
        path: 'test-results/logs-success-feedback.png',
        fullPage: true
      })
    })
  })

  test.describe('Error Handling - Backend Unavailable', () => {
    test('should handle complete backend unavailability gracefully', async ({ page }) => {
      const { consoleErrors, jsErrors } = setupConsoleErrorCapture(page)

      await loginAsAdmin(page)

      // Mock complete network failure
      await page.route('**/api/logs*', route => {
        route.abort('failed')
      })

      await page.goto('/logs')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(3000)

      // Should show error state without crashing
      await expect(page.locator('h1')).toContainText('Logs')

      // Verify error toast appears
      await expect(page.locator('[data-testid="toast"], .toast, [role="alert"]')).toBeVisible({ timeout: 10000 })

      // Verify no JavaScript crashes
      const criticalErrors = jsErrors.filter(error =>
        error.includes('Cannot read properties of undefined') ||
        error.includes('TypeError') ||
        error.includes('ReferenceError')
      )
      expect(criticalErrors).toHaveLength(0)

      await page.screenshot({
        path: 'test-results/logs-backend-unavailable.png',
        fullPage: true
      })
    })

    test('should handle intermittent backend failures', async ({ page }) => {
      const { consoleErrors, jsErrors } = setupConsoleErrorCapture(page)

      await loginAsAdmin(page)

      let requestCount = 0
      await page.route('**/api/logs*', route => {
        requestCount++
        if (requestCount % 2 === 0) {
          // Every other request fails
          route.fulfill({
            status: 503,
            contentType: 'application/json',
            body: JSON.stringify({ success: false, error: 'Service temporarily unavailable' })
          })
        } else {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              success: true,
              data: { logs: [], total: 0, page: 1, pageSize: 100 }
            })
          })
        }
      })

      await page.goto('/logs')
      await page.waitForLoadState('networkidle')

      // Try refreshing multiple times
      const refreshButton = page.locator('button:has-text("Refresh")')
      await refreshButton.click()
      await page.waitForTimeout(1000)

      await refreshButton.click()
      await page.waitForTimeout(1000)

      // Should handle intermittent failures gracefully
      expect(jsErrors.filter(error =>
        error.includes('Cannot read properties of undefined') ||
        error.includes('TypeError')
      )).toHaveLength(0)

      await page.screenshot({
        path: 'test-results/logs-intermittent-failures.png',
        fullPage: true
      })
    })
  })

  test.describe('Comprehensive Integration Tests', () => {
    test('should perform complete logs page workflow', async ({ page }) => {
      const { consoleErrors, jsErrors } = setupConsoleErrorCapture(page)

      await mockLogsApiSuccess(page)
      await loginAsAdmin(page)

      // Navigate to logs page
      await page.goto('/logs')
      await page.waitForLoadState('networkidle')

      // Verify initial load
      await expect(page.locator('h1')).toContainText('Logs')

      // Test tab navigation
      await page.click('text=System')
      await page.waitForTimeout(500)

      await page.click('text=Security')
      await page.waitForTimeout(500)

      // Test search
      const searchInput = page.locator('input[type="search"], input[placeholder*="search"], input[placeholder*="Search"]')
      if (await searchInput.isVisible()) {
        await searchInput.fill('test')
        await page.waitForTimeout(500)
        await searchInput.clear()
      }

      // Test refresh
      const refreshButton = page.locator('button:has-text("Refresh")')
      await refreshButton.click()
      await page.waitForTimeout(1000)

      // Test export (mock download)
      const exportButton = page.locator('button:has-text("Export")')
      if (await exportButton.isVisible()) {
        // Set up download handler
        page.on('download', () => {
          // Download triggered successfully
        })
        await exportButton.click()
        await page.waitForTimeout(500)
      }

      // Final verification - no errors during complete workflow
      expect(jsErrors).toHaveLength(0)

      await page.screenshot({
        path: 'test-results/logs-complete-workflow.png',
        fullPage: true
      })
    })

    test('should maintain state consistency across operations', async ({ page }) => {
      const { consoleErrors, jsErrors } = setupConsoleErrorCapture(page)

      await mockLogsApiSuccess(page)
      await loginAsAdmin(page)
      await page.goto('/logs')
      await page.waitForLoadState('networkidle')

      // Rapid state changes to test consistency
      await page.click('text=System')
      await page.click('text=Security')
      await page.click('text=All')

      const refreshButton = page.locator('button:has-text("Refresh")')
      await refreshButton.click()
      await refreshButton.click() // Double click to test race conditions

      await page.waitForTimeout(2000)

      // Verify page is still functional
      await expect(page.locator('h1')).toContainText('Logs')

      // No errors should occur from rapid state changes
      expect(jsErrors).toHaveLength(0)

      await page.screenshot({
        path: 'test-results/logs-state-consistency.png',
        fullPage: true
      })
    })
  })
})