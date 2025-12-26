/**
 * Applications Page Layout and UI Tests
 * 
 * Comprehensive testing of Applications page card layout, alignment,
 * responsive behavior, and visual consistency across different screen sizes.
 */

import { test, expect, Page, Locator } from '@playwright/test'

// Applications page test helpers
class ApplicationsPageHelper {
  constructor(private page: Page) {}

  async getApplicationCards(): Promise<Locator[]> {
    return await this.page.locator('[data-testid="application-card"], .bg-card.p-6.rounded-xl.border').all()
  }

  async getCategoryButtons(): Promise<Locator[]> {
    return await this.page.locator('button:has(p:text("All Apps")), button:has(p.font-medium.text-sm)').all()
  }

  async getCardGrid(): Promise<Locator> {
    return this.page.locator('.grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-3.gap-6')
  }

  async getCategoryGrid(): Promise<Locator> {
    return this.page.locator('.grid.grid-cols-2.md\\:grid-cols-3.lg\\:grid-cols-6.gap-4')
  }

  async assertCardAlignment(): Promise<void> {
    const cards = await this.getApplicationCards()
    const cardElements = await Promise.all(cards.map(card => card.boundingBox()))
    
    // Check that cards have consistent spacing
    if (cardElements.length > 1) {
      const firstCard = cardElements[0]
      const secondCard = cardElements[1]
      
      if (firstCard && secondCard) {
        // Cards should be aligned on the same row or have consistent gap
        const gap = secondCard.y - (firstCard.y + firstCard.height)
        expect(gap).toBeGreaterThanOrEqual(20) // Tailwind gap-6 = 24px, allowing for small variations
      }
    }
  }

  async assertResponsiveLayout(viewport: { width: number, height: number }): Promise<void> {
    await this.page.setViewportSize(viewport)
    await this.page.waitForLoadState('networkidle')
    
    const categoryGrid = await this.getCategoryGrid()
    const cardGrid = await this.getCardGrid()
    
    await expect(categoryGrid).toBeVisible()
    await expect(cardGrid).toBeVisible()
  }
}

test.describe('Applications Page Layout', () => {
  let appHelper: ApplicationsPageHelper

  test.beforeEach(async ({ page }) => {
    appHelper = new ApplicationsPageHelper(page)
    await page.goto('/applications')
    await page.waitForLoadState('networkidle')
  })

  test.describe('Page Structure and Layout', () => {
    test('should render applications page with correct structure', async ({ page }) => {
      // Check page title and description
      await expect(page.locator('h1:text("Application Marketplace")')).toBeVisible()
      await expect(page.locator('p:text("Discover and install applications")')).toBeVisible()

      // Check search functionality
      const searchInput = page.locator('input[placeholder*="Search applications"]')
      await expect(searchInput).toBeVisible()

      // Check filter button
      const filterButton = page.locator('button:has-text("Filters")')
      await expect(filterButton).toBeVisible()
    })

    test('should render category grid with proper alignment', async ({ page }) => {
      const categoryGrid = await appHelper.getCategoryGrid()
      await expect(categoryGrid).toBeVisible()
      await expect(categoryGrid).toHaveClass(/grid/)
      await expect(categoryGrid).toHaveClass(/gap-4/)

      // Check category buttons
      const categoryButtons = await appHelper.getCategoryButtons()
      expect(categoryButtons.length).toBeGreaterThan(0)

      // All Apps button should be present
      const allAppsButton = page.locator('button:has(p:text("All Apps"))')
      await expect(allAppsButton).toBeVisible()

      // Category buttons should have consistent styling
      for (const button of categoryButtons) {
        await expect(button).toHaveClass(/p-4/)
        await expect(button).toHaveClass(/rounded-xl/)
        await expect(button).toHaveClass(/border/)
        await expect(button).toHaveClass(/text-left/)
      }
    })

    test('should render application cards grid with proper layout', async ({ page }) => {
      const cardGrid = await appHelper.getCardGrid()
      await expect(cardGrid).toBeVisible()
      await expect(cardGrid).toHaveClass(/grid/)
      await expect(cardGrid).toHaveClass(/gap-6/)

      // Check application cards
      const cards = await appHelper.getApplicationCards()
      expect(cards.length).toBeGreaterThan(0)

      // Verify card structure
      for (const card of cards.slice(0, 3)) { // Test first 3 cards
        await expect(card).toBeVisible()
        await expect(card).toHaveClass(/bg-card/)
        await expect(card).toHaveClass(/p-6/)
        await expect(card).toHaveClass(/rounded-xl/)
        await expect(card).toHaveClass(/border/)
      }
    })

    test('should have consistent card heights', async ({ page }) => {
      const cards = await appHelper.getApplicationCards()
      const cardHeights = await Promise.all(
        cards.slice(0, 3).map(async card => {
          const box = await card.boundingBox()
          return box?.height || 0
        })
      )

      // Cards should have similar heights (allowing for content variation)
      if (cardHeights.length > 1) {
        const minHeight = Math.min(...cardHeights)
        const maxHeight = Math.max(...cardHeights)
        const heightDifference = maxHeight - minHeight
        
        // Allow up to 100px height difference for content variation
        expect(heightDifference).toBeLessThan(100)
      }
    })
  })

  test.describe('Card Content and Alignment', () => {
    test('should display application card content correctly', async ({ page }) => {
      const cards = await appHelper.getApplicationCards()
      const firstCard = cards[0]

      if (firstCard) {
        // Check card has application name
        const appName = firstCard.locator('h3')
        await expect(appName).toBeVisible()

        // Check card has description
        const description = firstCard.locator('p.text-sm.text-muted-foreground')
        await expect(description).toBeVisible()

        // Check card has category icon
        const categoryIcon = firstCard.locator('svg').first()
        await expect(categoryIcon).toBeVisible()

        // Check card has rating
        const rating = firstCard.locator('span:near(svg[data-lucide="star"])')
        await expect(rating).toBeVisible()

        // Check card has install button or installed status
        const actionButton = firstCard.locator('button').last()
        await expect(actionButton).toBeVisible()
      }
    })

    test('should maintain card grid alignment', async ({ page }) => {
      await appHelper.assertCardAlignment()
    })

    test('should handle card hover effects properly', async ({ page }) => {
      const cards = await appHelper.getApplicationCards()
      const firstCard = cards[0]

      if (firstCard) {
        // Hover over card
        await firstCard.hover()
        
        // Card should have hover class
        await expect(firstCard).toHaveClass(/card-hover/)
        
        // Wait for transition
        await page.waitForTimeout(300)
      }
    })
  })

  test.describe('Search and Filter Functionality', () => {
    test('should filter applications based on search', async ({ page }) => {
      const searchInput = page.locator('input[placeholder*="Search applications"]')
      
      // Get initial card count
      const initialCards = await appHelper.getApplicationCards()
      const initialCount = initialCards.length

      // Search for specific application
      await searchInput.fill('Plex')
      await page.waitForTimeout(500) // Wait for filter to apply

      // Check filtered results
      const filteredCards = await appHelper.getApplicationCards()
      
      // Should have fewer or equal cards after filtering
      expect(filteredCards.length).toBeLessThanOrEqual(initialCount)
    })

    test('should filter applications by category', async ({ page }) => {
      // Get initial card count
      const initialCards = await appHelper.getApplicationCards()
      const initialCount = initialCards.length

      // Click on a category (e.g., Media Server)
      const mediaCategory = page.locator('button:has(p:text("Media Server"))')
      if (await mediaCategory.count() > 0) {
        await mediaCategory.click()
        await page.waitForTimeout(500)

        // Check that category is selected
        await expect(mediaCategory).toHaveClass(/border-primary/)

        // Check filtered results
        const filteredCards = await appHelper.getApplicationCards()
        expect(filteredCards.length).toBeLessThanOrEqual(initialCount)
      }
    })
  })

  test.describe('Responsive Design', () => {
    test('should display correctly on desktop (1920x1080)', async ({ page }) => {
      await appHelper.assertResponsiveLayout({ width: 1920, height: 1080 })
      
      // Desktop should show more columns
      const cardGrid = await appHelper.getCardGrid()
      await expect(cardGrid).toHaveClass(/lg:grid-cols-3/)
    })

    test('should display correctly on tablet (768x1024)', async ({ page }) => {
      await appHelper.assertResponsiveLayout({ width: 768, height: 1024 })
      
      // Tablet should show medium columns
      const cardGrid = await appHelper.getCardGrid()
      await expect(cardGrid).toHaveClass(/md:grid-cols-2/)
    })

    test('should display correctly on mobile (375x812)', async ({ page }) => {
      await appHelper.assertResponsiveLayout({ width: 375, height: 812 })
      
      // Mobile should show single column
      const cardGrid = await appHelper.getCardGrid()
      await expect(cardGrid).toHaveClass(/grid-cols-1/)
    })

    test('should maintain category grid responsiveness', async ({ page }) => {
      // Test category grid on different screen sizes
      const viewports = [
        { width: 1920, height: 1080 }, // Desktop
        { width: 768, height: 1024 },  // Tablet
        { width: 375, height: 812 }    // Mobile
      ]

      for (const viewport of viewports) {
        await page.setViewportSize(viewport)
        await page.waitForLoadState('networkidle')

        const categoryGrid = await appHelper.getCategoryGrid()
        await expect(categoryGrid).toBeVisible()

        // Check that categories are still clickable
        const allAppsButton = page.locator('button:has(p:text("All Apps"))')
        await expect(allAppsButton).toBeVisible()
      }
    })
  })

  test.describe('Visual Consistency', () => {
    test('should maintain consistent spacing and typography', async ({ page }) => {
      // Check page spacing
      const mainContent = page.locator('main')
      await expect(mainContent).toHaveClass(/p-6/)

      // Check section spacing
      const pageContainer = page.locator('.space-y-8')
      await expect(pageContainer).toBeVisible()

      // Check title typography
      const title = page.locator('h1')
      await expect(title).toHaveClass(/text-3xl/)
      await expect(title).toHaveClass(/font-bold/)
    })

    test('should handle empty search results properly', async ({ page }) => {
      const searchInput = page.locator('input[placeholder*="Search applications"]')
      
      // Search for non-existent application
      await searchInput.fill('NonExistentApp123')
      await page.waitForTimeout(500)

      // Should show empty state
      const emptyState = page.locator(':text("No applications found")')
      await expect(emptyState).toBeVisible()

      // Should show helpful message
      const helpMessage = page.locator(':text("Try adjusting your search terms")')
      await expect(helpMessage).toBeVisible()
    })
  })

  test.describe('Animation and Performance', () => {
    test('should render cards without animations (static site)', async ({ page }) => {
      // Check that cards no longer have animation classes
      const cards = await appHelper.getApplicationCards()
      
      for (const card of cards.slice(0, 3)) {
        await expect(card).not.toHaveClass(/animate-scale-in/)
      }
    })

    test('should maintain performance with all applications loaded', async ({ page }) => {
      // Measure page load performance
      const startTime = Date.now()
      await page.goto('/applications')
      await page.waitForLoadState('networkidle')
      const loadTime = Date.now() - startTime

      // Page should load within reasonable time (5 seconds)
      expect(loadTime).toBeLessThan(5000)

      // All cards should be visible
      const cards = await appHelper.getApplicationCards()
      expect(cards.length).toBeGreaterThan(0)
    })
  })
})