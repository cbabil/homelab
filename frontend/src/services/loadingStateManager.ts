/**
 * Loading State Manager
 *
 * Manages loading states and error handling for data services.
 * Provides consistent state management across service operations.
 */

import { LoadingState } from '@/types/dataService'

export class LoadingStateManager {
  private loadingState: LoadingState

  constructor() {
    this.loadingState = {
      isLoading: false,
      error: null,
      lastUpdated: null
    }
  }

  /**
   * Set loading state
   */
  setLoading(isLoading: boolean, error: string | null = null): void {
    this.loadingState = {
      isLoading,
      error,
      lastUpdated: isLoading ? this.loadingState.lastUpdated : new Date()
    }
  }

  /**
   * Get current loading state
   */
  getLoadingState(): LoadingState {
    return { ...this.loadingState }
  }

  /**
   * Check if currently loading
   */
  isLoading(): boolean {
    return this.loadingState.isLoading
  }

  /**
   * Check if there's an error
   */
  hasError(): boolean {
    return this.loadingState.error !== null
  }

  /**
   * Get current error message
   */
  getError(): string | null {
    return this.loadingState.error
  }

  /**
   * Clear error state
   */
  clearError(): void {
    this.loadingState.error = null
  }

  /**
   * Reset all state
   */
  reset(): void {
    this.loadingState = {
      isLoading: false,
      error: null,
      lastUpdated: null
    }
  }
}