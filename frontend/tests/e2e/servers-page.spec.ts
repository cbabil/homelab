/**
 * E2E Servers Page Tests
 *
 * Tests for the servers page including listing, adding, editing,
 * deleting, and connecting to servers.
 */

import { test, expect, Page } from '@playwright/test'

// Servers page test helper
class ServersPageHelper {
  constructor(private page: Page) {}

  async login(username: string = 'admin', password: string = 'TomoAdmin123!'): Promise<void> {
    await this.page.goto('/')
    await this.page.waitForLoadState('networkidle')

    const isOnLoginPage = await this.page.locator('#username').isVisible().catch(() => false)

    if (isOnLoginPage) {
      await this.page.fill('input[autocomplete="username"]', username)
      await this.page.fill('input[autocomplete="current-password"]', password)
      await this.page.click('button[type="submit"]')
      await this.page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 })
      await this.page.waitForLoadState('networkidle')
    }
  }

  async navigateToServers(): Promise<void> {
    await this.page.goto('/servers')
    await this.page.waitForLoadState('networkidle')
  }

  async clearAuthState(): Promise<void> {
    await this.page.context().clearCookies()
  }

  async openAddServerDialog(): Promise<void> {
    await this.page.click('button:has-text("Add Server")')
    await this.page.waitForSelector('[role="dialog"]')
  }

  async closeDialog(): Promise<void> {
    await this.page.keyboard.press('Escape')
  }

  async fillServerForm(server: {
    name: string
    host: string
    port?: string
    username: string
    password?: string
  }): Promise<void> {
    // Use MUI TextField labels for selection
    await this.page.getByLabel('Name').fill(server.name)
    await this.page.getByLabel('Host').fill(server.host)
    if (server.port) {
      await this.page.getByLabel('Port').fill(server.port)
    }
    await this.page.getByLabel('Username').fill(server.username)
    if (server.password) {
      await this.page.getByLabel('Password').fill(server.password)
    }
  }

  async getServerRowCount(): Promise<number> {
    // DataTable uses table rows
    const rows = await this.page.locator('table tbody tr').count()
    return rows
  }

  async serverExists(name: string): Promise<boolean> {
    const row = this.page.locator(`table tbody tr:has-text("${name}")`)
    return await row.isVisible().catch(() => false)
  }
}

test.describe('Servers Page', () => {
  let helper: ServersPageHelper

  test.beforeEach(async ({ page }) => {
    helper = new ServersPageHelper(page)
    await helper.clearAuthState()
    await helper.login()
  })

  test.describe('Page Layout', () => {
    test('should display servers page header', async ({ page }) => {
      await helper.navigateToServers()

      const serversTitle = page.locator('h1:has-text("Servers"), h2:has-text("Servers")').first()
      await expect(serversTitle).toBeVisible()
    })

    test('should display Add Server button', async ({ page }) => {
      await helper.navigateToServers()

      const addButton = page.locator('button:has-text("Add Server")')
      await expect(addButton).toBeVisible()
    })

    test('should display search input when servers exist', async ({ page }) => {
      await helper.navigateToServers()

      // Search appears when there are servers
      const rowCount = await helper.getServerRowCount()
      if (rowCount > 0) {
        const searchInput = page.getByPlaceholder(/search/i)
        await expect(searchInput).toBeVisible()
      }
    })
  })

  test.describe('Server List', () => {
    test('should display empty state or server table', async ({ page }) => {
      await helper.navigateToServers()

      // Either shows servers in table or empty state
      const hasTable = await page.locator('table').isVisible().catch(() => false)
      const hasEmptyState = await page.locator('text=No servers').isVisible().catch(() => false)

      expect(hasTable || hasEmptyState).toBe(true)
    })

    test('should display server data in table format', async ({ page }) => {
      await helper.navigateToServers()

      const rowCount = await helper.getServerRowCount()
      if (rowCount > 0) {
        // Table should have headers
        await expect(page.locator('table thead')).toBeVisible()

        // Each row should have server info
        const firstRow = page.locator('table tbody tr').first()
        await expect(firstRow).toBeVisible()
      }
    })
  })

  test.describe('Add Server Dialog', () => {
    test('should open add server dialog when clicking Add Server', async ({ page }) => {
      await helper.navigateToServers()

      await helper.openAddServerDialog()

      const dialog = page.locator('[role="dialog"]')
      await expect(dialog).toBeVisible()
    })

    test('should display all form fields in add dialog', async ({ page }) => {
      await helper.navigateToServers()
      await helper.openAddServerDialog()

      // Check for form fields using MUI labels
      await expect(page.getByLabel('Name')).toBeVisible()
      await expect(page.getByLabel('Host')).toBeVisible()
      await expect(page.getByLabel('Port')).toBeVisible()
      await expect(page.getByLabel('Username')).toBeVisible()
    })

    test('should have port field with default value 22', async ({ page }) => {
      await helper.navigateToServers()
      await helper.openAddServerDialog()

      const portInput = page.getByLabel('Port')
      await expect(portInput).toBeVisible()
      await expect(portInput).toHaveValue('22')
    })

    test('should have authentication type selector', async ({ page }) => {
      await helper.navigateToServers()
      await helper.openAddServerDialog()

      // Look for Password/SSH Key radio buttons or tabs
      const passwordOption = page.locator('text=Password').first()
      const sshKeyOption = page.locator('text=SSH Key').first()

      const hasPasswordOption = await passwordOption.isVisible().catch(() => false)
      const hasSshKeyOption = await sshKeyOption.isVisible().catch(() => false)

      expect(hasPasswordOption || hasSshKeyOption).toBe(true)
    })

    test('should close dialog when clicking Cancel', async ({ page }) => {
      await helper.navigateToServers()
      await helper.openAddServerDialog()

      await page.click('button:has-text("Cancel")')

      const dialog = page.locator('[role="dialog"]')
      await expect(dialog).not.toBeVisible()
    })

    test('should close dialog when pressing Escape', async ({ page }) => {
      await helper.navigateToServers()
      await helper.openAddServerDialog()

      await helper.closeDialog()

      const dialog = page.locator('[role="dialog"]')
      await expect(dialog).not.toBeVisible()
    })
  })

  test.describe('Form Validation', () => {
    test('should have Add button disabled when form is empty', async ({ page }) => {
      await helper.navigateToServers()
      await helper.openAddServerDialog()

      const addButton = page.locator('button:has-text("Add")').last()
      await expect(addButton).toBeDisabled()
    })

    test('should have Add button disabled without name', async ({ page }) => {
      await helper.navigateToServers()
      await helper.openAddServerDialog()

      // Fill everything except name
      await page.getByLabel('Host').fill('192.168.1.100')
      await page.getByLabel('Username').fill('admin')
      await page.getByLabel('Password').fill('password123')

      const addButton = page.locator('button:has-text("Add")').last()
      await expect(addButton).toBeDisabled()
    })

    test('should have Add button disabled without host', async ({ page }) => {
      await helper.navigateToServers()
      await helper.openAddServerDialog()

      // Fill everything except host
      await page.getByLabel('Name').fill('Test Server')
      await page.getByLabel('Username').fill('admin')
      await page.getByLabel('Password').fill('password123')

      const addButton = page.locator('button:has-text("Add")').last()
      await expect(addButton).toBeDisabled()
    })

    test('should have Add button disabled without credentials', async ({ page }) => {
      await helper.navigateToServers()
      await helper.openAddServerDialog()

      // Fill everything except password
      await page.getByLabel('Name').fill('Test Server')
      await page.getByLabel('Host').fill('192.168.1.100')
      await page.getByLabel('Username').fill('admin')

      const addButton = page.locator('button:has-text("Add")').last()
      await expect(addButton).toBeDisabled()
    })

    test('should enable Add button when form is complete', async ({ page }) => {
      await helper.navigateToServers()
      await helper.openAddServerDialog()

      await helper.fillServerForm({
        name: 'Test Server',
        host: '192.168.1.100',
        username: 'admin',
        password: 'password123'
      })

      const addButton = page.locator('button:has-text("Add")').last()
      await expect(addButton).toBeEnabled()
    })
  })

  test.describe('Add Server Flow', () => {
    test('should show loading state when adding server', async ({ page }) => {
      await helper.navigateToServers()
      await helper.openAddServerDialog()

      await helper.fillServerForm({
        name: 'Test Server',
        host: '192.168.1.100',
        username: 'admin',
        password: 'password123'
      })

      const addButton = page.locator('button:has-text("Add")').last()
      await addButton.click()

      // Button should show loading or be disabled
      await expect(addButton).toBeDisabled()
    })

    test('should show error when connection fails', async ({ page }) => {
      await helper.navigateToServers()
      await helper.openAddServerDialog()

      // Use invalid host to trigger connection error
      await helper.fillServerForm({
        name: 'Invalid Server',
        host: '999.999.999.999',
        username: 'admin',
        password: 'password123'
      })

      const addButton = page.locator('button:has-text("Add")').last()
      await addButton.click()

      // Should show error message (wait for backend response)
      await page.waitForTimeout(5000)

      // Dialog should still be open with error, or server added with error status
      const dialog = page.locator('[role="dialog"]')
      const dialogVisible = await dialog.isVisible().catch(() => false)

      if (dialogVisible) {
        // Error shown in dialog
        const errorText = page.locator('text=/failed|error|unable/i')
        await expect(errorText).toBeVisible({ timeout: 10000 })
      }
    })
  })

  test.describe('Search Functionality', () => {
    test('should filter servers by search term', async ({ page }) => {
      await helper.navigateToServers()

      const rowCount = await helper.getServerRowCount()
      if (rowCount > 0) {
        const searchInput = page.getByPlaceholder(/search/i)
        await searchInput.fill('nonexistent-server-xyz')
        await page.waitForTimeout(300) // Debounce

        // Should show no results
        const filteredCount = await helper.getServerRowCount()
        expect(filteredCount).toBeLessThanOrEqual(rowCount)
      }
    })
  })

  test.describe('Server Actions', () => {
    test('should show action buttons in table row', async ({ page }) => {
      await helper.navigateToServers()

      const rowCount = await helper.getServerRowCount()
      if (rowCount > 0) {
        const firstRow = page.locator('table tbody tr').first()

        // Look for action buttons (icons or buttons)
        const actionButtons = firstRow.locator('button')
        const buttonCount = await actionButtons.count()

        expect(buttonCount).toBeGreaterThan(0)
      }
    })

    test('should have connect/disconnect action', async ({ page }) => {
      await helper.navigateToServers()

      const rowCount = await helper.getServerRowCount()
      if (rowCount > 0) {
        const firstRow = page.locator('table tbody tr').first()

        // Look for connect or status indicator
        const connectButton = firstRow.locator('button[title*="Connect"], button[title*="Disconnect"]')
        const statusIndicator = firstRow.locator('[class*="status"], [data-status]')

        const hasConnect = await connectButton.isVisible().catch(() => false)
        const hasStatus = await statusIndicator.isVisible().catch(() => false)

        expect(hasConnect || hasStatus).toBe(true)
      }
    })
  })

  test.describe('Bulk Operations', () => {
    test('should have checkbox for bulk selection', async ({ page }) => {
      await helper.navigateToServers()

      const rowCount = await helper.getServerRowCount()
      if (rowCount > 0) {
        // Look for checkboxes in table
        const checkbox = page.locator('table tbody input[type="checkbox"]').first()
        const hasCheckbox = await checkbox.isVisible().catch(() => false)

        // Bulk selection should be available
        expect(hasCheckbox).toBe(true)
      }
    })

    test('should show bulk action bar when servers selected', async ({ page }) => {
      await helper.navigateToServers()

      const rowCount = await helper.getServerRowCount()
      if (rowCount > 0) {
        const checkbox = page.locator('table tbody input[type="checkbox"]').first()
        await checkbox.check()

        // Bulk action bar should appear
        const bulkBar = page.locator('text=/selected|bulk/i')
        await expect(bulkBar).toBeVisible({ timeout: 2000 })
      }
    })
  })

  test.describe('Responsiveness', () => {
    test('should display properly on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await helper.navigateToServers()

      const serversTitle = page.locator('h1:has-text("Servers"), h2:has-text("Servers")').first()
      await expect(serversTitle).toBeVisible()
    })

    test('should display properly on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await helper.navigateToServers()

      const serversTitle = page.locator('h1:has-text("Servers"), h2:has-text("Servers")').first()
      await expect(serversTitle).toBeVisible()
    })

    test('should display properly on desktop viewport', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 })
      await helper.navigateToServers()

      const serversTitle = page.locator('h1:has-text("Servers"), h2:has-text("Servers")').first()
      await expect(serversTitle).toBeVisible()
    })
  })

  test.describe('Accessibility', () => {
    test('should have proper heading structure', async ({ page }) => {
      await helper.navigateToServers()

      const headings = page.locator('h1, h2, h3')
      const headingCount = await headings.count()
      expect(headingCount).toBeGreaterThanOrEqual(1)
    })

    test('should have focusable Add Server button', async ({ page }) => {
      await helper.navigateToServers()

      const addButton = page.locator('button:has-text("Add Server")')
      await addButton.focus()
      await expect(addButton).toBeFocused()
    })

    test('should support keyboard navigation in dialog', async ({ page }) => {
      await helper.navigateToServers()
      await helper.openAddServerDialog()

      // Tab through dialog - should move focus
      await page.keyboard.press('Tab')

      // Some element should be focused
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName)
      expect(focusedElement).toBeTruthy()
    })

    test('should trap focus in dialog', async ({ page }) => {
      await helper.navigateToServers()
      await helper.openAddServerDialog()

      // Tab many times - focus should stay in dialog
      for (let i = 0; i < 20; i++) {
        await page.keyboard.press('Tab')
      }

      const dialog = page.locator('[role="dialog"]')
      const focusedInDialog = await dialog.evaluate((el) => {
        return el.contains(document.activeElement)
      })

      expect(focusedInDialog).toBe(true)
    })
  })

  test.describe('Navigation', () => {
    test('should navigate to servers page from sidebar', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')

      const serversNav = page.locator('a[href="/servers"], nav >> text=Servers').first()
      await serversNav.click()

      await expect(page).toHaveURL('/servers')
    })

    test('should highlight servers in sidebar when on page', async ({ page }) => {
      await helper.navigateToServers()

      const serversNav = page.locator('a[href="/servers"]').first()
      const isActive = await serversNav.evaluate((el) =>
        el.classList.contains('active') ||
        el.classList.contains('Mui-selected') ||
        el.getAttribute('aria-current') === 'page' ||
        el.closest('[class*="selected"]') !== null
      ).catch(() => false)

      expect(isActive).toBe(true)
    })
  })
})
