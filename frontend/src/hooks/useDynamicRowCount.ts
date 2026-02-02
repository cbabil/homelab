/**
 * Dynamic Row Count Hook
 *
 * Calculates the optimal number of rows that fit in a container.
 */

import { useState, useEffect, RefObject } from 'react'

interface UseDynamicRowCountOptions {
  rowHeight?: number
  headerHeight?: number
  paginationHeight?: number
  minRows?: number
}

export function useDynamicRowCount(
  containerRef: RefObject<HTMLElement | null>,
  options: UseDynamicRowCountOptions = {}
) {
  const {
    rowHeight = 36,
    headerHeight = 48,
    paginationHeight = 52,
    minRows = 5
  } = options

  const [rowsPerPage, setRowsPerPage] = useState(minRows)

  useEffect(() => {
    const calculateRows = () => {
      if (!containerRef.current) return

      const containerHeight = containerRef.current.clientHeight
      if (containerHeight === 0) return // Skip if not yet laid out

      const availableHeight = containerHeight - headerHeight - paginationHeight
      const calculatedRows = Math.floor(availableHeight / rowHeight)
      const finalRows = Math.max(calculatedRows, minRows)

      setRowsPerPage(finalRows)
    }

    // Use requestAnimationFrame to ensure layout is complete
    const rafId = requestAnimationFrame(() => {
      calculateRows()
    })

    const resizeObserver = new ResizeObserver(() => {
      requestAnimationFrame(calculateRows)
    })

    if (containerRef.current) {
      resizeObserver.observe(containerRef.current)
    }

    return () => {
      cancelAnimationFrame(rafId)
      resizeObserver.disconnect()
    }
  }, [containerRef, rowHeight, headerHeight, paginationHeight, minRows])

  return rowsPerPage
}
