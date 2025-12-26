/**
 * Page Visibility Hook
 *
 * Custom hook that tracks page visibility using the Page Visibility API.
 * Returns true when the page is visible/active, false when hidden/inactive.
 */

import { useState, useEffect } from 'react'

export function usePageVisibility(): boolean {
  const [isVisible, setIsVisible] = useState<boolean>(() => {
    // Initialize with current visibility state
    if (typeof document !== 'undefined') {
      return !document.hidden
    }
    return true
  })

  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsVisible(!document.hidden)
    }

    // Add event listener for visibility changes
    document.addEventListener('visibilitychange', handleVisibilityChange)

    // Cleanup event listener on unmount
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [])

  return isVisible
}