# Task 11: Write E2E Tests

## Overview

Write end-to-end tests using Playwright to verify the complete NIST compliance workflow.

## Test File to Create

**File:** `frontend/tests/e2e/nist-password-compliance.spec.ts`

```typescript
/**
 * E2E Tests for NIST SP 800-63B-4 Password Compliance
 *
 * Tests the complete workflow of NIST compliance mode:
 * - Settings UI toggling
 * - Password validation behavior
 * - User registration with NIST rules
 */

import { test, expect } from '@playwright/test'

test.describe('NIST Password Compliance', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/login')
    await page.fill('[data-testid="username-input"]', 'admin')
    await page.fill('[data-testid="password-input"]', 'AdminPassword123!')
    await page.click('[data-testid="login-button"]')
    await page.waitForURL('/dashboard')
  })

  test.describe('Security Settings UI', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/settings')
      await page.click('[data-testid="security-tab"]')
    })

    test('should show NIST compliance toggle', async ({ page }) => {
      await expect(page.getByText('NIST SP 800-63B Compliance')).toBeVisible()
      await expect(page.locator('[data-testid="nist-compliance-toggle"]')).toBeVisible()
    })

    test('should hide complexity toggles when NIST mode enabled', async ({ page }) => {
      // Enable NIST mode
      await page.click('[data-testid="nist-compliance-toggle"]')

      // Complexity toggles should be hidden
      await expect(page.getByText('Require uppercase')).not.toBeVisible()
      await expect(page.getByText('Require numbers')).not.toBeVisible()
      await expect(page.getByText('Require special')).not.toBeVisible()

      // Expiration should be hidden
      await expect(page.getByText('Password expiration')).not.toBeVisible()
    })

    test('should show NIST-specific settings when enabled', async ({ page }) => {
      // Enable NIST mode
      await page.click('[data-testid="nist-compliance-toggle"]')

      // NIST-specific settings should be visible
      await expect(page.getByText('Password blocklist screening')).toBeVisible()
      await expect(page.getByText('Have I Been Pwned API')).toBeVisible()
    })

    test('should show complexity toggles when NIST mode disabled', async ({ page }) => {
      // Ensure NIST mode is off
      const toggle = page.locator('[data-testid="nist-compliance-toggle"]')
      if (await toggle.isChecked()) {
        await toggle.click()
      }

      // Legacy toggles should be visible
      await expect(page.getByText('Require uppercase')).toBeVisible()
      await expect(page.getByText('Require numbers')).toBeVisible()
      await expect(page.getByText('Require special')).toBeVisible()
      await expect(page.getByText('Password expiration')).toBeVisible()
    })

    test('should auto-adjust min length to 15 when NIST enabled', async ({ page }) => {
      // Set min length to 8 first (legacy mode)
      const minLengthInput = page.locator('[data-testid="password-min-length-input"]')
      await minLengthInput.fill('8')

      // Enable NIST mode
      await page.click('[data-testid="nist-compliance-toggle"]')

      // Min length should auto-adjust to 15
      await expect(minLengthInput).toHaveValue('15')
    })

    test('should show info banner in NIST mode', async ({ page }) => {
      await page.click('[data-testid="nist-compliance-toggle"]')

      await expect(page.getByRole('alert')).toContainText('NIST compliance mode')
    })

    test('should show warning banner in legacy mode', async ({ page }) => {
      // Ensure legacy mode
      const toggle = page.locator('[data-testid="nist-compliance-toggle"]')
      if (await toggle.isChecked()) {
        await toggle.click()
      }

      await expect(page.getByRole('alert')).toContainText('phased out')
    })

    test('should save NIST settings', async ({ page }) => {
      // Enable NIST mode and settings
      await page.click('[data-testid="nist-compliance-toggle"]')
      await page.click('[data-testid="blocklist-check-toggle"]')

      // Save
      await page.click('[data-testid="save-settings-button"]')

      // Verify success toast
      await expect(page.getByText('Security settings saved')).toBeVisible()

      // Reload and verify persistence
      await page.reload()
      await page.click('[data-testid="security-tab"]')

      await expect(page.locator('[data-testid="nist-compliance-toggle"]')).toBeChecked()
    })
  })

  test.describe('Password Validation - NIST Mode', () => {
    test.beforeEach(async ({ page }) => {
      // Enable NIST mode in settings
      await page.goto('/settings')
      await page.click('[data-testid="security-tab"]')

      const toggle = page.locator('[data-testid="nist-compliance-toggle"]')
      if (!(await toggle.isChecked())) {
        await toggle.click()
        await page.click('[data-testid="save-settings-button"]')
        await page.waitForSelector('text=Security settings saved')
      }

      // Logout
      await page.click('[data-testid="user-menu"]')
      await page.click('[data-testid="logout-button"]')
    })

    test('should accept 15+ char password without complexity', async ({ page }) => {
      await page.goto('/register')

      // Fill form with NIST-compliant password (no uppercase, no special)
      await page.fill('[data-testid="username-input"]', 'testuser')
      await page.fill('[data-testid="email-input"]', 'test@example.com')
      await page.fill('[data-testid="password-input"]', 'thisisaverylongpassphrase')
      await page.fill('[data-testid="confirm-password-input"]', 'thisisaverylongpassphrase')
      await page.click('[data-testid="accept-terms-checkbox"]')

      // Strength indicator should show valid
      await expect(page.locator('[data-testid="password-strength"]')).toContainText(/good|strong/i)

      // All requirement checks should be satisfied
      await expect(page.locator('[data-testid="req-min-length"] svg')).toHaveClass(/success/)
    })

    test('should reject password under 15 chars', async ({ page }) => {
      await page.goto('/register')

      await page.fill('[data-testid="password-input"]', 'shortpass')

      // Should show error
      await expect(page.getByText('at least 15 characters')).toBeVisible()
      await expect(page.locator('[data-testid="password-strength"]')).toContainText(/too short/i)
    })

    test('should reject password with sequential pattern', async ({ page }) => {
      await page.goto('/register')

      await page.fill('[data-testid="password-input"]', 'mypassword12345678')

      // Should show sequential pattern error
      await expect(page.getByText(/sequential/i)).toBeVisible()
    })

    test('should reject password with repetitive pattern', async ({ page }) => {
      await page.goto('/register')

      await page.fill('[data-testid="password-input"]', 'mypasswordaaaa!')

      // Should show repetitive pattern error
      await expect(page.getByText(/repetitive/i)).toBeVisible()
    })

    test('should reject common password', async ({ page }) => {
      await page.goto('/register')

      await page.fill('[data-testid="password-input"]', 'password123456789')

      // Should show common password error
      await expect(page.getByText(/common/i)).toBeVisible()
    })

    test('should show passphrase tip for short valid passwords', async ({ page }) => {
      await page.goto('/register')

      // Valid but could be longer (exactly 15 chars)
      await page.fill('[data-testid="password-input"]', 'fifteencharpass')

      // Should show passphrase tip
      await expect(page.getByText(/passphrase/i)).toBeVisible()
    })
  })

  test.describe('Password Validation - Legacy Mode', () => {
    test.beforeEach(async ({ page }) => {
      // Disable NIST mode
      await page.goto('/settings')
      await page.click('[data-testid="security-tab"]')

      const toggle = page.locator('[data-testid="nist-compliance-toggle"]')
      if (await toggle.isChecked()) {
        await toggle.click()
        await page.click('[data-testid="save-settings-button"]')
        await page.waitForSelector('text=Security settings saved')
      }

      // Logout
      await page.click('[data-testid="user-menu"]')
      await page.click('[data-testid="logout-button"]')
    })

    test('should require uppercase in legacy mode', async ({ page }) => {
      await page.goto('/register')

      // Password without uppercase
      await page.fill('[data-testid="password-input"]', 'password123!')

      // Should show uppercase requirement
      await expect(page.locator('[data-testid="req-uppercase"] svg')).not.toHaveClass(/success/)
    })

    test('should require numbers in legacy mode', async ({ page }) => {
      await page.goto('/register')

      // Password without numbers
      await page.fill('[data-testid="password-input"]', 'PasswordTest!')

      // Should show number requirement
      await expect(page.locator('[data-testid="req-number"] svg')).not.toHaveClass(/success/)
    })

    test('should require special chars in legacy mode', async ({ page }) => {
      await page.goto('/register')

      // Password without special chars
      await page.fill('[data-testid="password-input"]', 'PasswordTest123')

      // Should show special char requirement
      await expect(page.locator('[data-testid="req-special"] svg')).not.toHaveClass(/success/)
    })

    test('should accept complex password meeting all requirements', async ({ page }) => {
      await page.goto('/register')

      // Fully compliant legacy password
      await page.fill('[data-testid="password-input"]', 'MyPassword123!')

      // All requirements should be met
      await expect(page.locator('[data-testid="req-min-length"] svg')).toHaveClass(/success/)
      await expect(page.locator('[data-testid="req-uppercase"] svg')).toHaveClass(/success/)
      await expect(page.locator('[data-testid="req-lowercase"] svg')).toHaveClass(/success/)
      await expect(page.locator('[data-testid="req-number"] svg')).toHaveClass(/success/)
      await expect(page.locator('[data-testid="req-special"] svg')).toHaveClass(/success/)
    })
  })

  test.describe('Mode Switching', () => {
    test('should switch from legacy to NIST mode', async ({ page }) => {
      await page.goto('/settings')
      await page.click('[data-testid="security-tab"]')

      // Start in legacy mode
      const toggle = page.locator('[data-testid="nist-compliance-toggle"]')
      if (await toggle.isChecked()) {
        await toggle.click()
        await page.click('[data-testid="save-settings-button"]')
        await page.waitForSelector('text=Security settings saved')
      }

      // Verify legacy UI
      await expect(page.getByText('Require uppercase')).toBeVisible()

      // Switch to NIST mode
      await toggle.click()

      // Verify NIST UI (complexity toggles hidden)
      await expect(page.getByText('Require uppercase')).not.toBeVisible()
      await expect(page.getByText('Password blocklist screening')).toBeVisible()
    })

    test('should preserve settings after mode switch', async ({ page }) => {
      await page.goto('/settings')
      await page.click('[data-testid="security-tab"]')

      // Set some legacy settings
      const toggle = page.locator('[data-testid="nist-compliance-toggle"]')
      if (await toggle.isChecked()) {
        await toggle.click()
      }

      // Set lockout duration (should persist across modes)
      await page.selectOption('[data-testid="lockout-duration-select"]', '1800')
      await page.click('[data-testid="save-settings-button"]')
      await page.waitForSelector('text=Security settings saved')

      // Switch to NIST mode
      await toggle.click()
      await page.click('[data-testid="save-settings-button"]')
      await page.waitForSelector('text=Security settings saved')

      // Verify lockout duration preserved
      await expect(page.locator('[data-testid="lockout-duration-select"]')).toHaveValue('1800')
    })
  })
})
```

## Test Data Setup

Create test fixtures in `frontend/tests/e2e/fixtures/`:

```typescript
// fixtures/test-users.ts
export const testUsers = {
  admin: {
    username: 'admin',
    password: 'AdminPassword123!',
    email: 'admin@example.com'
  }
}
```

## Run Commands

```bash
# Run all NIST E2E tests
cd frontend
npx playwright test nist-password-compliance.spec.ts

# Run with UI mode for debugging
npx playwright test nist-password-compliance.spec.ts --ui

# Run specific test
npx playwright test -g "should show NIST compliance toggle"
```

## Test IDs to Add

The tests assume these `data-testid` attributes exist in components:

| Test ID | Component |
|---------|-----------|
| `nist-compliance-toggle` | NIST mode toggle switch |
| `blocklist-check-toggle` | Blocklist toggle switch |
| `password-min-length-input` | Min length number input |
| `save-settings-button` | Save button |
| `security-tab` | Security tab in settings |
| `password-strength` | Password strength indicator |
| `req-min-length` | Minimum length requirement item |
| `req-uppercase` | Uppercase requirement item |
| `req-number` | Number requirement item |
| `req-special` | Special char requirement item |
| `username-input` | Username field |
| `password-input` | Password field |
| `confirm-password-input` | Confirm password field |
| `accept-terms-checkbox` | Terms checkbox |
| `user-menu` | User dropdown menu |
| `logout-button` | Logout button |

## Dependencies

- All implementation tasks (01-09) must be complete
- Test database with admin user
- Playwright configured

## Acceptance Criteria

- [ ] All E2E tests pass
- [ ] Tests cover both NIST and legacy modes
- [ ] Tests verify UI changes on mode switch
- [ ] Tests verify password validation behavior
- [ ] Tests verify settings persistence
- [ ] No flaky tests
- [ ] Tests run in < 2 minutes
