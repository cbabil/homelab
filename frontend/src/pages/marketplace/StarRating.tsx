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

const sizeClasses: Record<StarSize, string> = {
  sm: 'h-3 w-3',
  md: 'h-4 w-4',
  lg: 'h-5 w-5',
}

const textSizeClasses: Record<StarSize, string> = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-base',
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
    const starClass = sizeClasses[size]
    const isHovering = hoverRating !== null && starIndex < hoverRating

    // For interactive mode, use full stars only (no half stars on hover)
    if (interactive && hoverRating !== null) {
      return (
        <Star
          key={starIndex}
          className={`${starClass} transition-all ${
            isHovering
              ? 'text-yellow-500 fill-yellow-500'
              : 'text-gray-300 dark:text-gray-600'
          }`}
        />
      )
    }

    // Display mode with half-star support
    if (fillPercentage === 100) {
      return (
        <Star
          key={starIndex}
          className={`${starClass} text-yellow-500 fill-yellow-500`}
        />
      )
    } else if (fillPercentage === 0) {
      return (
        <Star
          key={starIndex}
          className={`${starClass} text-gray-300 dark:text-gray-600`}
        />
      )
    } else {
      // Half-star using gradient
      return (
        <div key={starIndex} className="relative inline-block">
          <Star
            className={`${starClass} text-gray-300 dark:text-gray-600`}
          />
          <div
            className="absolute top-0 left-0 overflow-hidden"
            style={{ width: `${fillPercentage}%` }}
          >
            <Star
              className={`${starClass} text-yellow-500 fill-yellow-500`}
            />
          </div>
        </div>
      )
    }
  }

  return (
    <div className="flex items-center space-x-1">
      <div
        className={`flex items-center space-x-0.5 ${
          interactive ? 'cursor-pointer' : ''
        }`}
        onMouseLeave={handleMouseLeave}
      >
        {Array.from({ length: maxStars }, (_, i) => (
          <button
            key={i}
            type="button"
            disabled={!interactive}
            onClick={() => handleClick(i)}
            onMouseEnter={() => handleMouseEnter(i)}
            className={`${
              interactive
                ? 'hover:scale-110 transition-transform'
                : 'cursor-default'
            } focus:outline-none`}
            aria-label={`Rate ${i + 1} stars`}
          >
            {renderStar(i)}
          </button>
        ))}
      </div>

      {showCount && ratingCount > 0 && (
        <span className={`text-muted-foreground ${textSizeClasses[size]}`}>
          ({ratingCount})
        </span>
      )}
    </div>
  )
}
