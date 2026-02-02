/**
 * Navigation Section Component
 *
 * Grouping component for navigation items with optional header and dividers.
 * Supports collapsible sections and improved visual organization.
 */

import { memo, ReactNode } from 'react'
import { Box } from '@mui/material'
import { Button } from '@/components/ui/Button'

interface NavigationSectionProps {
  title?: string
  children: ReactNode
  className?: string
  collapsible?: boolean
  isCollapsed?: boolean
  onToggle?: () => void
  showDivider?: boolean
}

export const NavigationSection = memo(({
  title,
  children,
  className,
  collapsible = false,
  isCollapsed = false,
  onToggle,
  showDivider = false
}: NavigationSectionProps) => {
  return (
    <Box className={className}>
      {showDivider && (
        <Box sx={{ mx: 1.5, my: 2, borderTop: 1, borderColor: 'rgba(var(--border-rgb), 0.5)' }} />
      )}

      {title && (
        <Box sx={{ px: 1.5, mb: 1 }}>
          {collapsible ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggle}
              className="text-muted-foreground hover:text-foreground"
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                width: '100%',
                px: 1,
                py: 0.5,
                height: 'auto',
                fontSize: '0.75rem',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}
              aria-expanded={!isCollapsed}
              aria-controls={`nav-section-${title.toLowerCase().replace(/\s+/g, '-')}`}
            >
              <span>{title}</span>
              <Box
                component="svg"
                sx={{
                  width: 12,
                  height: 12,
                  transition: 'transform 0.2s',
                  transform: isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)'
                }}
                viewBox="0 0 12 12"
                fill="currentColor"
              >
                <path d="M6 8L2 4h8l-4 4z" />
              </Box>
            </Button>
          ) : (
            <Box
              component="h3"
              sx={{
                px: 1,
                py: 0.5,
                fontSize: '0.75rem',
                fontWeight: 600,
                color: 'hsl(var(--muted-foreground))',
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}
            >
              {title}
            </Box>
          )}
        </Box>
      )}

      <Box
        id={title ? `nav-section-${title.toLowerCase().replace(/\s+/g, '-')}` : undefined}
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 0.5,
          ...(collapsible && {
            maxHeight: isCollapsed ? 0 : 'none',
            overflow: isCollapsed ? 'hidden' : 'visible',
            opacity: isCollapsed ? 0 : 1,
            transition: 'all 0.3s ease-in-out'
          })
        }}
      >
        {children}
      </Box>
    </Box>
  )
})

NavigationSection.displayName = 'NavigationSection'