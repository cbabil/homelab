/**
 * Smoke Tests - Basic frontend verification
 *
 * Minimal tests that verify the frontend builds and loads correctly.
 * These tests work without any backend by disabling API mocking.
 */

import { test, expect } from '@playwright/test'

// Increase timeout for smoke tests since we're waiting for app to load
test.setTimeout(60000)

test.describe('Smoke Tests', () => {
  test.describe('Basic Loading', () => {
    test('should load the index page', async ({ page }) => {
      // Navigate and wait for any response
      const response = await page.goto('/', { waitUntil: 'commit' })

      // Page should respond
      expect(response?.status()).toBeLessThan(500)
    })

    test('should have HTML structure', async ({ page }) => {
      await page.goto('/', { waitUntil: 'domcontentloaded' })

      // Should have basic HTML elements
      const html = page.locator('html')
      await expect(html).toBeVisible()

      const body = page.locator('body')
      await expect(body).toBeVisible()

      // Should have the root element for React
      const root = page.locator('#root')
      await expect(root).toBeVisible()
    })

    test('should have a title', async ({ page }) => {
      await page.goto('/', { waitUntil: 'domcontentloaded' })

      const title = await page.title()
      expect(title.length).toBeGreaterThan(0)
    })

    test('should not have critical JS errors', async ({ page }) => {
      const criticalErrors: string[] = []

      page.on('pageerror', (error) => {
        // Only track truly critical errors
        if (
          error.message.includes('SyntaxError') ||
          error.message.includes('ReferenceError') ||
          error.message.includes('TypeError')
        ) {
          criticalErrors.push(error.message)
        }
      })

      await page.goto('/', { waitUntil: 'domcontentloaded' })

      // Allow time for JS to execute
      await page.waitForTimeout(2000)

      // Filter out errors from network failures (expected without backend)
      const actualErrors = criticalErrors.filter(
        (e) => !e.includes('fetch') && !e.includes('network') && !e.includes('Failed to')
      )

      expect(actualErrors).toHaveLength(0)
    })
  })

  test.describe('Static Assets', () => {
    test('should load CSS files', async ({ page }) => {
      const failedCss: string[] = []

      page.on('requestfailed', (request) => {
        if (request.url().endsWith('.css')) {
          failedCss.push(request.url())
        }
      })

      await page.goto('/', { waitUntil: 'domcontentloaded' })

      expect(failedCss).toHaveLength(0)
    })

    test('should load JavaScript bundles', async ({ page }) => {
      const failedJs: string[] = []

      page.on('requestfailed', (request) => {
        const url = request.url()
        if (url.endsWith('.js') || url.endsWith('.mjs')) {
          failedJs.push(url)
        }
      })

      await page.goto('/', { waitUntil: 'domcontentloaded' })

      expect(failedJs).toHaveLength(0)
    })
  })

  test.describe('Basic Accessibility', () => {
    test('should have lang attribute', async ({ page }) => {
      await page.goto('/', { waitUntil: 'domcontentloaded' })

      const lang = await page.locator('html').getAttribute('lang')
      expect(lang).toBeTruthy()
    })

    test('should have viewport meta tag', async ({ page }) => {
      await page.goto('/', { waitUntil: 'domcontentloaded' })

      const viewport = page.locator('meta[name="viewport"]')
      await expect(viewport).toHaveCount(1)
    })
  })

  test.describe('Responsive Design', () => {
    test('should render on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/', { waitUntil: 'domcontentloaded' })

      // Page should be scrollable or fit in viewport
      const body = page.locator('body')
      const box = await body.boundingBox()
      expect(box?.width).toBeGreaterThan(0)
    })

    test('should render on desktop viewport', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 })
      await page.goto('/', { waitUntil: 'domcontentloaded' })

      const body = page.locator('body')
      const box = await body.boundingBox()
      expect(box?.width).toBeGreaterThan(0)
    })
  })

  test.describe('Performance', () => {
    test('should load DOM within timeout', async ({ page }) => {
      const start = Date.now()

      await page.goto('/', { waitUntil: 'domcontentloaded' })

      const duration = Date.now() - start

      // Should load within 10 seconds
      expect(duration).toBeLessThan(10000)
    })
  })
})
