/**
 * Login Page E2E Tests
 *
 * Tests for the login page functionality including form validation,
 * error handling, and successful login flow.
 */

import { test, expect } from '@playwright/test'

test.describe('Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    // Wait for page to fully load
    await page.waitForSelector('button:has-text("Sign In")', { timeout: 10000 })
  })

  test.describe('Page Structure', () => {
    test('should display login form elements', async ({ page }) => {
      // Logo
      await expect(page.getByRole('img', { name: 'Tomo Logo' })).toBeVisible()

      // Heading
      await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()

      // Form fields
      await expect(page.getByRole('textbox', { name: 'Username' })).toBeVisible()
      await expect(page.getByRole('textbox', { name: 'Password' })).toBeVisible()

      // Remember me checkbox
      await expect(page.getByRole('checkbox', { name: 'Remember me' })).toBeVisible()

      // Forgot password link
      await expect(page.getByRole('link', { name: 'Forgot Password?' })).toBeVisible()

      // Sign in button
      await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible()

      // Create account link
      await expect(page.getByRole('link', { name: 'Create account' })).toBeVisible()

      // Copyright footer
      await expect(page.getByText(/© \d{4} Tomo/)).toBeVisible()
    })

    test('should have Sign In button disabled when form is empty', async ({ page }) => {
      const signInButton = page.getByRole('button', { name: 'Sign In' })
      await expect(signInButton).toBeDisabled()
    })
  })

  test.describe('Form Validation', () => {
    test('should enable Sign In button when both fields are filled', async ({ page }) => {
      await page.getByRole('textbox', { name: 'Username' }).fill('testuser')
      await page.getByRole('textbox', { name: 'Password' }).fill('testpassword')

      const signInButton = page.getByRole('button', { name: 'Sign In' })
      await expect(signInButton).toBeEnabled()
    })

    test('should keep button disabled with only username', async ({ page }) => {
      await page.getByRole('textbox', { name: 'Username' }).fill('testuser')

      const signInButton = page.getByRole('button', { name: 'Sign In' })
      await expect(signInButton).toBeDisabled()
    })

    test('should keep button disabled with only password', async ({ page }) => {
      await page.getByRole('textbox', { name: 'Password' }).fill('testpassword')

      const signInButton = page.getByRole('button', { name: 'Sign In' })
      await expect(signInButton).toBeDisabled()
    })
  })

  test.describe('Password Visibility Toggle', () => {
    test('should toggle password visibility', async ({ page }) => {
      const passwordField = page.getByRole('textbox', { name: 'Password' })
      const toggleButton = page.getByRole('button', { name: /password/i })

      // Initially password type
      await expect(passwordField).toHaveAttribute('type', 'password')

      // Click to show
      await toggleButton.click()
      await expect(passwordField).toHaveAttribute('type', 'text')

      // Click to hide
      await toggleButton.click()
      await expect(passwordField).toHaveAttribute('type', 'password')
    })
  })

  test.describe('Login Error Handling', () => {
    test('should display error message on invalid credentials', async ({ page }) => {
      await page.getByRole('textbox', { name: 'Username' }).fill('wronguser')
      await page.getByRole('textbox', { name: 'Password' }).fill('wrongpassword')

      await page.getByRole('button', { name: 'Sign In' }).click()

      // Wait for error message
      await expect(page.getByText('Invalid username or password')).toBeVisible({ timeout: 10000 })
    })

    test('should preserve form values after failed login', async ({ page }) => {
      const username = 'testuser'
      const password = 'testpassword'

      await page.getByRole('textbox', { name: 'Username' }).fill(username)
      await page.getByRole('textbox', { name: 'Password' }).fill(password)

      await page.getByRole('button', { name: 'Sign In' }).click()

      // Wait for error
      await expect(page.getByText('Invalid username or password')).toBeVisible({ timeout: 10000 })

      // Values should be preserved
      await expect(page.getByRole('textbox', { name: 'Username' })).toHaveValue(username)
      await expect(page.getByRole('textbox', { name: 'Password' })).toHaveValue(password)
    })

    test('should clear error message when user types', async ({ page }) => {
      // First trigger an error
      await page.getByRole('textbox', { name: 'Username' }).fill('wronguser')
      await page.getByRole('textbox', { name: 'Password' }).fill('wrongpassword')
      await page.getByRole('button', { name: 'Sign In' }).click()

      await expect(page.getByText('Invalid username or password')).toBeVisible({ timeout: 10000 })

      // Type in username field
      await page.getByRole('textbox', { name: 'Username' }).fill('newuser')

      // Error should be cleared (hidden)
      await expect(page.getByText('Invalid username or password')).not.toBeVisible()
    })
  })

  test.describe('Remember Me', () => {
    test('should toggle remember me checkbox', async ({ page }) => {
      const checkbox = page.getByRole('checkbox', { name: 'Remember me' })

      // Initially unchecked
      await expect(checkbox).not.toBeChecked()

      // Click to check
      await checkbox.click()
      await expect(checkbox).toBeChecked()

      // Click to uncheck
      await checkbox.click()
      await expect(checkbox).not.toBeChecked()
    })
  })

  test.describe('Navigation Links', () => {
    test('should navigate to forgot password page', async ({ page }) => {
      await page.getByRole('link', { name: 'Forgot Password?' }).click()
      await expect(page).toHaveURL(/.*forgot-password/)
    })

    test('should navigate to registration page', async ({ page }) => {
      await page.getByRole('link', { name: 'Create account' }).click()
      await expect(page).toHaveURL(/.*register/)
    })
  })

  test.describe('No Visual Flicker', () => {
    test('should not have DOM changes on failed login', async ({ page }) => {
      // Set up DOM change observer
      await page.evaluate(() => {
        (window as Window & { _domChanges: Array<{ type: string; tag: string }> })._domChanges = []
        const observer = new MutationObserver((mutations) => {
          mutations.forEach((mutation) => {
            if (mutation.type === 'childList') {
              mutation.removedNodes.forEach((node) => {
                if ((node as Element).nodeType === 1) {
                  (window as Window & { _domChanges: Array<{ type: string; tag: string }> })._domChanges.push({
                    type: 'REMOVED',
                    tag: (node as Element).tagName
                  })
                }
              })
              mutation.addedNodes.forEach((node) => {
                if ((node as Element).nodeType === 1) {
                  (window as Window & { _domChanges: Array<{ type: string; tag: string }> })._domChanges.push({
                    type: 'ADDED',
                    tag: (node as Element).tagName
                  })
                }
              })
            }
          })
        })
        observer.observe(document.body, { childList: true, subtree: true })
      })

      // Fill form and submit
      await page.getByRole('textbox', { name: 'Username' }).fill('wronguser')
      await page.getByRole('textbox', { name: 'Password' }).fill('wrongpassword')

      // Clear changes from typing
      await page.evaluate(() => {
        (window as Window & { _domChanges: Array<{ type: string; tag: string }> })._domChanges = []
      })

      // Click sign in
      await page.getByRole('button', { name: 'Sign In' }).click()

      // Wait for response
      await page.waitForTimeout(2000)

      // Check DOM changes - should be empty (no spinner, no card remount)
      const changes = await page.evaluate(() => {
        return (window as Window & { _domChanges: Array<{ type: string; tag: string }> })._domChanges
      })

      // Should have no DOM changes (error uses visibility, not add/remove)
      expect(changes).toHaveLength(0)
    })

    test('should not have input field disabled state changes on failed login', async ({ page }) => {
      // Set up observer for Mui-disabled class changes on form elements
      await page.evaluate(() => {
        (window as Window & { _styleChanges: Array<{ tag: string; change: string }> })._styleChanges = []
        const observer = new MutationObserver((mutations) => {
          mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
              const target = mutation.target as Element
              if (target.tagName === 'INPUT' || target.tagName === 'LABEL') {
                const oldVal = (mutation.oldValue || '') as string
                const newVal = target.getAttribute('class') || ''
                if (oldVal.includes('Mui-disabled') !== newVal.includes('Mui-disabled')) {
                  (window as Window & { _styleChanges: Array<{ tag: string; change: string }> })._styleChanges.push({
                    tag: target.tagName,
                    change: newVal.includes('Mui-disabled') ? 'DISABLED' : 'ENABLED'
                  })
                }
              }
            }
          })
        })
        observer.observe(document.body, {
          subtree: true,
          attributes: true,
          attributeOldValue: true,
          attributeFilter: ['class']
        })
      })

      // Fill form and submit
      await page.getByRole('textbox', { name: 'Username' }).fill('wronguser')
      await page.getByRole('textbox', { name: 'Password' }).fill('wrongpassword')

      // Clear changes from typing
      await page.evaluate(() => {
        (window as Window & { _styleChanges: Array<{ tag: string; change: string }> })._styleChanges = []
      })

      // Click sign in
      await page.getByRole('button', { name: 'Sign In' }).click()

      // Wait for response
      await page.waitForTimeout(2000)

      // Check style changes - should be empty for inputs and labels
      const changes = await page.evaluate(() => {
        return (window as Window & { _styleChanges: Array<{ tag: string; change: string }> })._styleChanges
      })

      // Should have no disabled state changes on input fields or labels
      expect(changes).toHaveLength(0)
    })

    test('should have no CSS transitions on form elements', async ({ page }) => {
      // Check that button has no transitions
      const buttonStyles = await page.evaluate(() => {
        const button = document.querySelector('button[type="submit"]')
        if (!button) return null
        const styles = window.getComputedStyle(button)
        return {
          transition: styles.transition,
          transitionDuration: styles.transitionDuration
        }
      })

      expect(buttonStyles).not.toBeNull()
      expect(buttonStyles?.transition).toBe('none')
      expect(buttonStyles?.transitionDuration).toBe('0s')

      // Check that input fields have no transitions
      const inputStyles = await page.evaluate(() => {
        const inputs = document.querySelectorAll('input')
        return Array.from(inputs).map(input => {
          const styles = window.getComputedStyle(input)
          return {
            transition: styles.transition,
            transitionDuration: styles.transitionDuration
          }
        })
      })

      inputStyles.forEach(style => {
        expect(style.transitionDuration).toBe('0s')
      })
    })
  })
})
