/**
 * Star Rating Component
 *
 * Interactive star rating component with:
 * - Display mode: Show filled/empty stars based on rating
 * - Interactive mode: Click to set rating (1-5 stars)
 * - Hover state in interactive mode
 * - Support for half-star display for fractional ratings
 * - Configurable size: 'sm' | 'md' | 'lg'
 */

import { useState } from 'react'
import { Star } from 'lucide-react'
import { Box } from '@mui/material'

type StarSize = 'sm' | 'md' | 'lg'

interface StarRatingProps {
  rating: number
  maxStars?: number
  size?: StarSize
  interactive?: boolean
  onRatingChange?: (rating: number) => void
  showCount?: boolean
  ratingCount?: number
}

const sizeMap: Record<StarSize, number> = {
  sm: 12,
  md: 16,
  lg: 20,
}

const textSizeMap: Record<StarSize, string> = {
  sm: '0.75rem',
  md: '0.875rem',
  lg: '1rem',
}

export function StarRating({
  rating,
  maxStars = 5,
  size = 'md',
  interactive = false,
  onRatingChange,
  showCount = false,
  ratingCount = 0,
}: StarRatingProps) {
  const [hoverRating, setHoverRating] = useState<number | null>(null)

  const displayRating = hoverRating !== null ? hoverRating : rating

  const handleClick = (starIndex: number) => {
    if (interactive && onRatingChange) {
      onRatingChange(starIndex + 1)
    }
  }

  const handleMouseEnter = (starIndex: number) => {
    if (interactive) {
      setHoverRating(starIndex + 1)
    }
  }

  const handleMouseLeave = () => {
    if (interactive) {
      setHoverRating(null)
    }
  }

  const getStarFillPercentage = (starIndex: number): number => {
    const diff = displayRating - starIndex

    if (diff >= 1) {
      return 100
    } else if (diff > 0) {
      return diff * 100
    } else {
      return 0
    }
  }

  const renderStar = (starIndex: number) => {
    const fillPercentage = getStarFillPercentage(starIndex)
    const starSize = sizeMap[size]
    const isHovering = hoverRating !== null && starIndex < hoverRating

    // For interactive mode, use full stars only (no half stars on hover)
    if (interactive && hoverRating !== null) {
      return (
        <Star
          key={starIndex}
          style={{
            width: starSize,
            height: starSize,
            transition: 'all 0.2s',
            color: isHovering ? '#eab308' : '#d1d5db',
            fill: isHovering ? '#eab308' : 'none'
          }}
        />
      )
    }

    // Display mode with half-star support
    if (fillPercentage === 100) {
      return (
        <Star
          key={starIndex}
          style={{
            width: starSize,
            height: starSize,
            color: '#eab308',
            fill: '#eab308'
          }}
        />
      )
    } else if (fillPercentage === 0) {
      return (
        <Star
          key={starIndex}
          style={{
            width: starSize,
            height: starSize,
            color: '#d1d5db'
          }}
        />
      )
    } else {
      // Half-star using gradient
      return (
        <Box key={starIndex} sx={{ position: 'relative', display: 'inline-block' }}>
          <Star
            style={{
              width: starSize,
              height: starSize,
              color: '#d1d5db'
            }}
          />
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              overflow: 'hidden',
              width: `${fillPercentage}%`
            }}
          >
            <Star
              style={{
                width: starSize,
                height: starSize,
                color: '#eab308',
                fill: '#eab308'
              }}
            />
          </Box>
        </Box>
      )
    }
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 0.25,
          cursor: interactive ? 'pointer' : 'default'
        }}
        onMouseLeave={handleMouseLeave}
      >
        {Array.from({ length: maxStars }, (_, i) => (
          <Box
            key={i}
            component="button"
            type="button"
            disabled={!interactive}
            onClick={() => handleClick(i)}
            onMouseEnter={() => handleMouseEnter(i)}
            sx={{
              background: 'none',
              border: 'none',
              padding: 0,
              cursor: interactive ? 'pointer' : 'default',
              transition: 'transform 0.2s',
              '&:hover': interactive ? { transform: 'scale(1.1)' } : {},
              '&:focus': { outline: 'none' }
            }}
            aria-label={`Rate ${i + 1} stars`}
          >
            {renderStar(i)}
          </Box>
        ))}
      </Box>

      {showCount && ratingCount > 0 && (
        <Box component="span" sx={{ color: 'text.secondary', fontSize: textSizeMap[size] }}>
          ({ratingCount})
        </Box>
      )}
    </Box>
  )
}
