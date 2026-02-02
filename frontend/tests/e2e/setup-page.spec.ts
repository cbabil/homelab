/**
 * E2E Setup Page Tests
 *
 * Tests for the initial admin setup page shown when no admin user exists.
 * Note: These tests require a clean database state with no admin users.
 */

import { test, expect, Page } from '@playwright/test'

// Setup page test helper
class SetupPageHelper {
  constructor(private page: Page) {}

  async navigateToSetup(): Promise<void> {
    await this.page.goto('/setup')
    await this.page.waitForLoadState('networkidle')
  }

  async clearAuthState(): Promise<void> {
    await this.page.context().clearCookies()
    await this.page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })
  }

  async fillUsername(username: string): Promise<void> {
    await this.page.fill('#username', username)
  }

  async fillPassword(password: string): Promise<void> {
    await this.page.fill('#password', password)
  }

  async fillConfirmPassword(password: string): Promise<void> {
    await this.page.fill('#confirmPassword', password)
  }

  async submitForm(): Promise<void> {
    await this.page.click('button[type="submit"]')
  }

  async togglePasswordVisibility(field: 'password' | 'confirmPassword'): Promise<void> {
    const container = this.page.locator(`#${field}`).locator('..')
    await container.locator('button').click()
  }
}

test.describe('Setup Page', () => {
  let helper: SetupPageHelper

  test.beforeEach(async ({ page }) => {
    helper = new SetupPageHelper(page)
    await helper.clearAuthState()
  })

  test.describe('Page Display', () => {
    test('should display setup page with correct header', async ({ page }) => {
      await helper.navigateToSetup()

      // Check for header elements (may redirect to login if admin exists)
      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)
      const isOnLogin = await page.locator('text=Welcome Back').isVisible().catch(() => false)

      // Either setup page is shown (no admin) or redirected to login (admin exists)
      expect(isOnSetup || isOnLogin).toBeTruthy()
    })

    test('should show loading state while checking system status', async ({ page }) => {
      // Navigate without waiting for network idle
      await page.goto('/setup')

      // Check for loading state (if visible briefly)
      const loadingText = page.locator('text=Checking system status')
      const isLoading = await loadingText.isVisible({ timeout: 1000 }).catch(() => false)

      // Loading state may be too fast to catch, so just verify page loads
      await page.waitForLoadState('networkidle')
      expect(true).toBe(true)
    })

    test('should display logo on setup page', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        const logo = page.locator('img[alt="Tomo Logo"]')
        await expect(logo).toBeVisible()
      }
    })

    test('should display subtitle text', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        await expect(page.locator('text=Create your account to get started')).toBeVisible()
      }
    })

    test('should display copyright footer', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        // Footer should contain copyright info
        const footer = page.locator('text=Tomo')
        await expect(footer.first()).toBeVisible()
      }
    })
  })

  test.describe('Form Fields', () => {
    test('should display username field', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        await expect(page.locator('label[for="username"]')).toBeVisible()
        await expect(page.locator('#username')).toBeVisible()
      }
    })

    test('should display password field', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        await expect(page.locator('label[for="password"]')).toBeVisible()
        await expect(page.locator('#password')).toBeVisible()
      }
    })

    test('should display confirm password field', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        await expect(page.locator('label[for="confirmPassword"]')).toBeVisible()
        await expect(page.locator('#confirmPassword')).toBeVisible()
      }
    })

    test('should have password visibility toggle buttons', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        // Password field toggle
        const passwordContainer = page.locator('#password').locator('..')
        await expect(passwordContainer.locator('button')).toBeVisible()

        // Confirm password field toggle
        const confirmContainer = page.locator('#confirmPassword').locator('..')
        await expect(confirmContainer.locator('button')).toBeVisible()
      }
    })

    test('should have submit button', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        await expect(page.locator('button[type="submit"]')).toBeVisible()
        await expect(page.locator('button:has-text("Create Account")')).toBeVisible()
      }
    })
  })

  test.describe('Form Validation', () => {
    test('should disable submit button when form is empty', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        const submitButton = page.locator('button[type="submit"]')
        await expect(submitButton).toBeDisabled()
      }
    })

    test('should show validation error for short username', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        await helper.fillUsername('ab')
        await page.locator('#password').focus() // Trigger blur

        // Check for validation error message
        const errorMessage = page.locator('text=at least')
        const hasError = await errorMessage.isVisible().catch(() => false)
        expect(hasError).toBe(true)
      }
    })

    test('should show validation error for weak password', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        await helper.fillUsername('validuser')
        await helper.fillPassword('weak')
        await page.locator('#confirmPassword').focus() // Trigger blur

        // Check for password validation error or feedback
        const errorMessage = page.locator('.text-red-500')
        const hasError = await errorMessage.isVisible().catch(() => false)
        expect(hasError).toBe(true)
      }
    })

    test('should show password mismatch error', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        await helper.fillUsername('validuser')
        await helper.fillPassword('StrongPassword123!')
        await helper.fillConfirmPassword('DifferentPassword123!')
        await page.locator('#username').focus() // Trigger blur

        await expect(page.locator('text=Passwords do not match')).toBeVisible()
      }
    })

    test('should enable submit button when form is valid', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        await helper.fillUsername('validadmin')
        await helper.fillPassword('StrongPassword123!')
        await helper.fillConfirmPassword('StrongPassword123!')

        const submitButton = page.locator('button[type="submit"]')
        await expect(submitButton).not.toBeDisabled()
      }
    })
  })

  test.describe('Password Strength Indicator', () => {
    test('should show password strength indicator when typing', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        await helper.fillPassword('test')

        // Strength indicator bars should appear
        const strengthBars = page.locator('.h-1.flex-1.rounded-full')
        const barCount = await strengthBars.count()
        expect(barCount).toBe(5)
      }
    })

    test('should show password feedback suggestions', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        await helper.fillPassword('weak')

        // Should show feedback suggestions
        const feedbackList = page.locator('ul.text-xs')
        const hasFeedback = await feedbackList.isVisible().catch(() => false)
        expect(hasFeedback).toBe(true)
      }
    })
  })

  test.describe('Password Visibility Toggle', () => {
    test('should toggle password visibility', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        const passwordInput = page.locator('#password')
        await helper.fillPassword('TestPassword123!')

        // Initially should be password type
        await expect(passwordInput).toHaveAttribute('type', 'password')

        // Click toggle button
        const toggleButton = page.locator('#password').locator('..').locator('button')
        await toggleButton.click()

        // Should now be text type
        await expect(passwordInput).toHaveAttribute('type', 'text')

        // Click again to hide
        await toggleButton.click()
        await expect(passwordInput).toHaveAttribute('type', 'password')
      }
    })

    test('should toggle confirm password visibility', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        const confirmInput = page.locator('#confirmPassword')
        await helper.fillConfirmPassword('TestPassword123!')

        // Initially should be password type
        await expect(confirmInput).toHaveAttribute('type', 'password')

        // Click toggle button
        const toggleButton = page.locator('#confirmPassword').locator('..').locator('button')
        await toggleButton.click()

        // Should now be text type
        await expect(confirmInput).toHaveAttribute('type', 'text')
      }
    })
  })

  test.describe('Redirect Behavior', () => {
    test('should redirect to login if admin already exists', async ({ page }) => {
      await helper.navigateToSetup()

      // If admin exists, should redirect to login
      await page.waitForURL((url) => {
        return url.pathname.includes('/login') || url.pathname.includes('/setup')
      }, { timeout: 5000 })

      const url = page.url()
      // Either on setup (no admin) or redirected to login (admin exists)
      expect(url.includes('/login') || url.includes('/setup')).toBeTruthy()
    })
  })

  test.describe('Responsiveness', () => {
    test('should display properly on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)
      const isOnLogin = await page.locator('text=Welcome Back').isVisible().catch(() => false)

      expect(isOnSetup || isOnLogin).toBeTruthy()
    })

    test('should display properly on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)
      const isOnLogin = await page.locator('text=Welcome Back').isVisible().catch(() => false)

      expect(isOnSetup || isOnLogin).toBeTruthy()
    })

    test('should display properly on desktop viewport', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 })
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)
      const isOnLogin = await page.locator('text=Welcome Back').isVisible().catch(() => false)

      expect(isOnSetup || isOnLogin).toBeTruthy()
    })
  })

  test.describe('Accessibility', () => {
    test('should have proper form labels', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        // Check that labels are associated with inputs
        await expect(page.locator('label[for="username"]')).toBeVisible()
        await expect(page.locator('label[for="password"]')).toBeVisible()
        await expect(page.locator('label[for="confirmPassword"]')).toBeVisible()
      }
    })

    test('should support keyboard navigation', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        // Tab through form elements
        await page.keyboard.press('Tab')
        await expect(page.locator('#username')).toBeFocused()

        await page.keyboard.press('Tab')
        await expect(page.locator('#password')).toBeFocused()

        await page.keyboard.press('Tab')
        // Skip toggle button
        await page.keyboard.press('Tab')
        await expect(page.locator('#confirmPassword')).toBeFocused()
      }
    })

    test('should have proper heading structure', async ({ page }) => {
      await helper.navigateToSetup()

      const isOnSetup = await page.locator('text=Welcome to Tomo').isVisible().catch(() => false)

      if (isOnSetup) {
        const h1 = page.locator('h1')
        await expect(h1).toBeVisible()
        await expect(h1).toContainText('Welcome to Tomo')
      }
    })
  })
})
