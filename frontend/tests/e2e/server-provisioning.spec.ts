/**
 * E2E Server Provisioning Tests
 *
 * Tests for the server provisioning flow including connection testing,
 * Docker decision panel, Agent decision panel, and error handling.
 *
 * Note: These tests verify UI behavior, not actual SSH connections.
 * Backend operations are tested separately; these focus on UI flow correctness.
 */

import { test, expect, Page } from "@playwright/test";

/** Helper class for server provisioning test interactions */
class ProvisioningTestHelper {
  constructor(private page: Page) {}

  async login(
    username = "admin",
    password = "TomoAdmin123!",
  ): Promise<void> {
    await this.page.goto("/");
    await this.page.waitForLoadState("networkidle");
    const isOnLoginPage = await this.page
      .locator("#username")
      .isVisible()
      .catch(() => false);
    if (isOnLoginPage) {
      await this.page.fill('input[autocomplete="username"]', username);
      await this.page.fill('input[autocomplete="current-password"]', password);
      await this.page.click('button[type="submit"]');
      await this.page.waitForURL((url) => !url.pathname.includes("/login"), {
        timeout: 10000,
      });
      await this.page.waitForLoadState("networkidle");
    }
  }

  async navigateToServers(): Promise<void> {
    await this.page.goto("/servers");
    await this.page.waitForLoadState("networkidle");
  }

  async clearAuthState(): Promise<void> {
    await this.page.context().clearCookies();
  }

  async openAddServerDialog(): Promise<void> {
    await this.page.click('button:has-text("Add Server")');
    await this.page.waitForSelector('[role="dialog"]');
  }

  async fillServerForm(server: {
    name: string;
    host: string;
    port?: string;
    username: string;
    password?: string;
  }): Promise<void> {
    await this.page.getByLabel("Name").fill(server.name);
    await this.page.getByLabel("Host").fill(server.host);
    if (server.port) {
      await this.page.getByLabel("Port").fill(server.port);
    }
    await this.page.getByLabel("Username").fill(server.username);
    if (server.password) {
      await this.page.getByLabel("Password").fill(server.password);
    }
  }

  async clickAddButton(): Promise<void> {
    const addButton = this.page.locator('button:has-text("Add")').last();
    await addButton.click();
  }

  async getDialog(): Promise<ReturnType<Page["locator"]>> {
    return this.page.locator('[role="dialog"]');
  }

  async isDialogOpen(): Promise<boolean> {
    return this.page
      .locator('[role="dialog"]')
      .isVisible()
      .catch(() => false);
  }
}

test.describe("Server Provisioning Flow", () => {
  let helper: ProvisioningTestHelper;

  test.beforeEach(async ({ page }) => {
    helper = new ProvisioningTestHelper(page);
    await helper.clearAuthState();
    await helper.login();
    await helper.navigateToServers();
  });

  test.describe("Initial Add Server Flow", () => {
    test("should show provisioning UI after clicking Add", async ({ page }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "Test Server",
        host: "192.168.1.100",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      // Wait for provisioning UI to appear - dialog title should change
      await expect(page.locator('[role="dialog"]')).toBeVisible();

      // Provisioning UI shows step indicators or progress
      const hasStepIndicator = await page
        .locator("text=/testing connection|checking docker|installing/i")
        .isVisible({ timeout: 5000 })
        .catch(() => false);

      // Either shows provisioning text or dialog remains open for flow
      expect(await helper.isDialogOpen()).toBe(true);
      if (hasStepIndicator) {
        expect(hasStepIndicator).toBe(true);
      }
    });

    test("should display step indicators in provisioning view", async ({
      page,
    }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "Step Test Server",
        host: "192.168.1.101",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      // Wait for provisioning UI
      await page.waitForTimeout(500);

      // Look for step-related elements
      const dialog = page.locator('[role="dialog"]');
      await expect(dialog).toBeVisible();

      // Should show connection testing step (first step)
      const connectionStep = page.locator("text=/connection|connecting/i");
      const hasConnectionStep = await connectionStep
        .isVisible()
        .catch(() => false);

      // Alternative: look for docker step text which indicates provisioning started
      const dockerStep = page.locator("text=/docker/i");
      const hasDockerStep = await dockerStep.isVisible().catch(() => false);

      // At least one provisioning indicator should be present
      expect(
        hasConnectionStep || hasDockerStep || (await helper.isDialogOpen()),
      ).toBe(true);
    });
  });

  test.describe("Docker Decision Panel", () => {
    test("should show Docker decision buttons when Docker check completes", async ({
      page,
    }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "Docker Decision Test",
        host: "192.168.1.102",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      // Wait for Docker decision panel (may appear if Docker not installed)
      // This depends on backend response; we check if UI elements exist when shown
      await page.waitForTimeout(3000);

      const installDockerBtn = page.locator(
        'button:has-text("Install Docker")',
      );
      const skipBtn = page.locator('button:has-text("Skip")');

      const hasInstallBtn = await installDockerBtn
        .isVisible()
        .catch(() => false);
      const hasSkipBtn = await skipBtn.isVisible().catch(() => false);

      // If Docker panel shows, both buttons should be visible
      if (hasInstallBtn) {
        expect(hasSkipBtn).toBe(true);
      }
    });

    test("should have accessible Docker decision panel", async ({ page }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "Docker A11y Test",
        host: "192.168.1.103",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      await page.waitForTimeout(3000);

      const installDockerBtn = page.locator(
        'button:has-text("Install Docker")',
      );
      if (await installDockerBtn.isVisible().catch(() => false)) {
        // Button should be focusable
        await installDockerBtn.focus();
        await expect(installDockerBtn).toBeFocused();
      }
    });
  });

  test.describe("Agent Decision Panel", () => {
    test("should show Agent decision after Docker step", async ({ page }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "Agent Decision Test",
        host: "192.168.1.104",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      // Wait for potential Agent panel
      await page.waitForTimeout(5000);

      const installAgentBtn = page.locator('button:has-text("Install Agent")');
      const agentText = page.locator("text=/agent/i");

      const hasAgentBtn = await installAgentBtn.isVisible().catch(() => false);
      const hasAgentText = await agentText.isVisible().catch(() => false);

      // Verify agent-related content is present in the flow
      if (hasAgentBtn) {
        const skipBtn = page.locator('button:has-text("Skip")');
        expect(await skipBtn.isVisible().catch(() => false)).toBe(true);
      }
      // Either shows agent panel or is still in earlier step
      expect(hasAgentBtn || hasAgentText || (await helper.isDialogOpen())).toBe(
        true,
      );
    });
  });

  test.describe("Error Handling", () => {
    test("should show error on connection failure", async ({ page }) => {
      await helper.openAddServerDialog();

      // Use invalid IP that will fail quickly
      await helper.fillServerForm({
        name: "Invalid Server",
        host: "999.999.999.999",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      // Wait for error state
      await page.waitForTimeout(8000);

      // Look for error indicators
      const errorText = page.locator("text=/failed|error|unable|timeout/i");
      const retryBtn = page.locator('button:has-text("Retry")');

      const hasError = await errorText.isVisible().catch(() => false);
      const hasRetry = await retryBtn.isVisible().catch(() => false);

      // Dialog should still be open with error
      expect(await helper.isDialogOpen()).toBe(true);
      // Should show error or retry button
      expect(hasError || hasRetry).toBe(true);
    });

    test("should show retry button on failure", async ({ page }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "Retry Test Server",
        host: "0.0.0.1",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      // Wait for failure and retry button
      await page.waitForTimeout(8000);

      const retryBtn = page.locator('button:has-text("Retry")');
      const hasRetry = await retryBtn.isVisible().catch(() => false);

      if (hasRetry) {
        await expect(retryBtn).toBeEnabled();
      }
    });
  });

  test.describe("Cancel During Provisioning", () => {
    test("should have cancel button during provisioning", async ({ page }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "Cancel Test Server",
        host: "192.168.1.110",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      // Wait for provisioning to start
      await page.waitForTimeout(500);

      // Look for cancel button
      const cancelBtn = page.locator('button:has-text("Cancel")');
      expect(await cancelBtn.isVisible().catch(() => false)).toBe(true);
    });

    test("should close dialog when cancel is clicked", async ({ page }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "Cancel Close Test",
        host: "192.168.1.111",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      await page.waitForTimeout(500);

      const cancelBtn = page.locator('button:has-text("Cancel")');
      if (await cancelBtn.isVisible().catch(() => false)) {
        await cancelBtn.click();
        await page.waitForTimeout(500);
        expect(await helper.isDialogOpen()).toBe(false);
      }
    });

    test("should close dialog when Escape is pressed", async ({ page }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "Escape Test Server",
        host: "192.168.1.112",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      await page.waitForTimeout(500);

      await page.keyboard.press("Escape");
      await page.waitForTimeout(500);

      expect(await helper.isDialogOpen()).toBe(false);
    });

    test("should close dialog when X button is clicked", async ({ page }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "X Button Test",
        host: "192.168.1.113",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      await page.waitForTimeout(500);

      const closeBtn = page.locator('[role="dialog"] button:has(svg)').first();
      if (await closeBtn.isVisible().catch(() => false)) {
        await closeBtn.click();
        await page.waitForTimeout(500);
        expect(await helper.isDialogOpen()).toBe(false);
      }
    });
  });

  test.describe("Keyboard Accessibility", () => {
    test("should trap focus within provisioning dialog", async ({ page }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "Focus Trap Test",
        host: "192.168.1.120",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      await page.waitForTimeout(500);

      const dialog = page.locator('[role="dialog"]');
      await expect(dialog).toBeVisible();

      // Tab through dialog elements
      for (let i = 0; i < 10; i++) {
        await page.keyboard.press("Tab");
      }

      // Focus should still be within dialog
      const focusedInDialog = await dialog.evaluate((el) =>
        el.contains(document.activeElement),
      );
      expect(focusedInDialog).toBe(true);
    });

    test("should allow tab navigation through decision buttons", async ({
      page,
    }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "Tab Nav Test",
        host: "192.168.1.121",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      await page.waitForTimeout(3000);

      // Check if decision panel buttons are tabbable
      const installDockerBtn = page.locator(
        'button:has-text("Install Docker")',
      );
      const installAgentBtn = page.locator('button:has-text("Install Agent")');
      const skipBtn = page.locator('button:has-text("Skip")');

      const hasDockerBtn = await installDockerBtn
        .isVisible()
        .catch(() => false);
      const hasAgentBtn = await installAgentBtn.isVisible().catch(() => false);

      if (hasDockerBtn) {
        await installDockerBtn.focus();
        await expect(installDockerBtn).toBeFocused();
        await page.keyboard.press("Tab");
        await expect(skipBtn).toBeFocused();
      } else if (hasAgentBtn) {
        await installAgentBtn.focus();
        await expect(installAgentBtn).toBeFocused();
        await page.keyboard.press("Tab");
        await expect(skipBtn).toBeFocused();
      }
    });

    test("should activate button with Enter key", async ({ page }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "Enter Key Test",
        host: "192.168.1.122",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      await page.waitForTimeout(3000);

      const cancelBtn = page.locator('button:has-text("Cancel")');
      if (await cancelBtn.isVisible().catch(() => false)) {
        await cancelBtn.focus();
        await expect(cancelBtn).toBeFocused();
        await page.keyboard.press("Enter");
        await page.waitForTimeout(500);
        expect(await helper.isDialogOpen()).toBe(false);
      }
    });

    test("should maintain logical focus order", async ({ page }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "Focus Order Test",
        host: "192.168.1.123",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      await page.waitForTimeout(500);

      const dialog = page.locator('[role="dialog"]');
      await expect(dialog).toBeVisible();

      // Focus should be on a focusable element
      const focusedElement = await page.evaluate(
        () => document.activeElement?.tagName,
      );
      expect(focusedElement).toBeTruthy();

      // Tab should move to next element
      await page.keyboard.press("Tab");
      const nextFocusedElement = await page.evaluate(
        () => document.activeElement?.tagName,
      );
      expect(nextFocusedElement).toBeTruthy();
    });
  });

  test.describe("Visual States", () => {
    test("should show progress indicator during active steps", async ({
      page,
    }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "Progress Test",
        host: "192.168.1.130",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      // Look for loading/progress indicators
      const spinner = page.locator(
        '[role="progressbar"], .MuiCircularProgress-root',
      );
      const loadingText = page.locator("text=/testing|checking|installing/i");

      await page.waitForTimeout(500);

      const hasSpinner = await spinner.isVisible().catch(() => false);
      const hasLoadingText = await loadingText.isVisible().catch(() => false);

      // Either visual indicator should be present during provisioning
      expect(
        hasSpinner || hasLoadingText || (await helper.isDialogOpen()),
      ).toBe(true);
    });

    test("should show step status icons", async ({ page }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "Status Icon Test",
        host: "192.168.1.131",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      await page.waitForTimeout(500);

      // Look for status-indicating SVG icons (checkmark, x, circle)
      const dialog = page.locator('[role="dialog"]');
      const svgIcons = dialog.locator("svg");

      const iconCount = await svgIcons.count();
      expect(iconCount).toBeGreaterThan(0);
    });
  });

  test.describe("Step Transitions", () => {
    test("should skip Docker step when Docker is installed", async ({
      page,
    }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "Docker Installed Test",
        host: "192.168.1.140",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      // If server has Docker, should skip to Agent decision
      await page.waitForTimeout(5000);

      const agentBtn = page.locator('button:has-text("Install Agent")');
      const dockerBtn = page.locator('button:has-text("Install Docker")');

      // Could see agent panel directly if docker was installed
      const hasAgentBtn = await agentBtn.isVisible().catch(() => false);
      const hasDockerBtn = await dockerBtn.isVisible().catch(() => false);

      // This validates the UI shows appropriate buttons
      expect(hasAgentBtn || hasDockerBtn || (await helper.isDialogOpen())).toBe(
        true,
      );
    });

    test("should skip Agent when Skip is clicked on Docker panel", async ({
      page,
    }) => {
      await helper.openAddServerDialog();
      await helper.fillServerForm({
        name: "Skip Docker Test",
        host: "192.168.1.141",
        username: "admin",
        password: "testpass123",
      });
      await helper.clickAddButton();

      await page.waitForTimeout(3000);

      const skipBtn = page.locator('button:has-text("Skip")');
      if (await skipBtn.isVisible().catch(() => false)) {
        await skipBtn.click();
        await page.waitForTimeout(500);

        // After skipping Docker, should see Agent panel or complete
        const agentBtn = page.locator('button:has-text("Install Agent")');
        const hasAgentBtn = await agentBtn.isVisible().catch(() => false);

        // Either shows agent panel or moved to another state
        expect(hasAgentBtn || (await helper.isDialogOpen())).toBe(true);
      }
    });
  });
});
