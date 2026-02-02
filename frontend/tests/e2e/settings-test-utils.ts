/**
 * Shared Test Utilities for Settings E2E Tests
 *
 * Common helpers and configuration for all settings tab tests.
 */

import { type Page } from '@playwright/test'

// Test configuration
export const TEST_CONFIG = {
  BACKEND_URL: 'http://localhost:8000',
  FRONTEND_URL: 'http://localhost:3001',
  ADMIN_USERNAME: 'admin',
  ADMIN_PASSWORD: 'TomoAdmin123!'
}

/**
 * Login to the application
 */
export async function login(page: Page) {
  await page.waitForSelector('input[placeholder*="username"]', { timeout: 10000 })
  await page.fill('input[placeholder*="username"]', TEST_CONFIG.ADMIN_USERNAME)
  await page.fill('input[placeholder*="password"]', TEST_CONFIG.ADMIN_PASSWORD)
  await page.click('button:has-text("Sign In")')
  await page.waitForSelector('text=NAVIGATION', { timeout: 15000 })
}

/**
 * Navigate to settings page (with login if needed)
 */
export async function navigateToSettings(page: Page) {
  await page.goto(`${TEST_CONFIG.FRONTEND_URL}/settings`)

  // Wait for either login page or settings page
  await Promise.race([
    page.waitForSelector('input[placeholder*="username"]', { timeout: 5000 }),
    page.waitForSelector('button:has-text("General")', { timeout: 5000 })
  ]).catch(() => {})

  // Login if needed
  const usernameInput = page.locator('input[placeholder*="username"]')
  if (await usernameInput.isVisible().catch(() => false)) {
    await login(page)
    await page.goto(`${TEST_CONFIG.FRONTEND_URL}/settings`)
  }

  // Wait for settings tabs
  await page.waitForSelector('button:has-text("General")', { timeout: 10000 })
}

/**
 * Click a settings tab by name
 * Uses a more specific selector to target the tab navigation buttons
 */
export async function clickSettingsTab(page: Page, tabName: string) {
  // The settings tabs are in a container with specific styling (flex space-x-1 bg-muted)
  // Target the button within the settings tab navigation area
  const tabNav = page.locator('.bg-muted.rounded-lg').first()
  const tabButton = tabNav.locator(`button:has-text("${tabName}")`)
  await tabButton.waitFor({ state: 'visible' })
  await tabButton.click()
  await page.waitForTimeout(500) // Allow tab content to load
}

/**
 * Get the value of a select dropdown
 */
export async function getSelectValue(page: Page, selector: string): Promise<string> {
  return await page.locator(selector).inputValue()
}

/**
 * Check if a toggle is checked
 */
export async function isToggleChecked(page: Page, label: string): Promise<boolean> {
  const row = page.locator(`text=${label}`).locator('..')
  const toggle = row.locator('button[role="switch"]')
  const ariaChecked = await toggle.getAttribute('aria-checked')
  return ariaChecked === 'true'
}

/**
 * Toggle a switch by its label
 */
export async function toggleSwitch(page: Page, label: string) {
  const row = page.locator(`text=${label}`).locator('..')
  const toggle = row.locator('button[role="switch"]')
  await toggle.click()
}
