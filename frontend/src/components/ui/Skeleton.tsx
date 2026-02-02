/**
 * Skeleton Loading Components
 *
 * Placeholder components that show content structure during loading.
 * Better UX than spinners as users can see where content will appear.
 */

import MuiSkeleton from '@mui/material/Skeleton'
import Box from '@mui/material/Box'
import Stack from '@mui/material/Stack'
import { SxProps, Theme } from '@mui/material/styles'

interface SkeletonProps {
  sx?: SxProps<Theme>
}

/**
 * Basic skeleton element with pulse animation
 */
export function Skeleton({ sx }: SkeletonProps) {
  return (
    <MuiSkeleton
      variant="rounded"
      animation="pulse"
      sx={{
        borderRadius: 1.5,
        ...sx,
      }}
    />
  )
}

/**
 * Skeleton for text lines
 */
export function SkeletonText({ sx, lines = 1 }: SkeletonProps & { lines?: number }) {
  return (
    <Stack spacing={1} sx={sx}>
      {Array.from({ length: lines }).map((_, i) => (
        <MuiSkeleton
          key={i}
          variant="text"
          animation="pulse"
          sx={{
            height: 16,
            width: i === lines - 1 && lines > 1 ? '75%' : '100%',
          }}
        />
      ))}
    </Stack>
  )
}

/**
 * Skeleton for circular avatars
 */
export function SkeletonAvatar({ sx, size = 'md' }: SkeletonProps & { size?: 'sm' | 'md' | 'lg' }) {
  const sizeMap = {
    sm: 32,
    md: 40,
    lg: 48,
  }

  return (
    <MuiSkeleton
      variant="circular"
      animation="pulse"
      width={sizeMap[size]}
      height={sizeMap[size]}
      sx={sx}
    />
  )
}

/**
 * Skeleton for cards
 */
export function SkeletonCard({ sx }: SkeletonProps) {
  return (
    <Box
      sx={{
        borderRadius: 3,
        border: 1,
        borderColor: 'divider',
        bgcolor: 'background.paper',
        p: 2,
        ...sx,
      }}
    >
      <Stack spacing={2}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <SkeletonAvatar />
          <Stack spacing={1} sx={{ flex: 1 }}>
            <MuiSkeleton variant="text" width="33%" height={16} />
            <MuiSkeleton variant="text" width="50%" height={12} />
          </Stack>
        </Box>
        <SkeletonText lines={3} />
      </Stack>
    </Box>
  )
}

/**
 * Skeleton for table rows
 */
export function SkeletonTableRow({ columns = 4, sx }: SkeletonProps & { columns?: number }) {
  return (
    <Box
      component="tr"
      sx={{
        borderBottom: 1,
        borderColor: 'divider',
        ...sx,
      }}
    >
      {Array.from({ length: columns }).map((_, i) => (
        <Box component="td" key={i} sx={{ p: 2 }}>
          <MuiSkeleton variant="text" width="100%" height={16} />
        </Box>
      ))}
    </Box>
  )
}

/**
 * Skeleton for stats/metric cards
 */
export function SkeletonStat({ sx }: SkeletonProps) {
  return (
    <Box
      sx={{
        borderRadius: 3,
        border: 1,
        borderColor: 'divider',
        bgcolor: 'background.paper',
        p: 2,
        ...sx,
      }}
    >
      <MuiSkeleton variant="text" width="50%" height={16} sx={{ mb: 1 }} />
      <MuiSkeleton variant="text" width="33%" height={32} />
    </Box>
  )
}

/**
 * Skeleton for server cards in grid
 */
export function SkeletonServerCard({ sx }: SkeletonProps) {
  return (
    <Box
      sx={{
        borderRadius: 3,
        border: 1,
        borderColor: 'divider',
        bgcolor: 'background.paper',
        p: 2,
        ...sx,
      }}
    >
      <Stack spacing={1.5}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <MuiSkeleton variant="rounded" width={40} height={40} sx={{ borderRadius: 2 }} />
            <Stack spacing={0.75}>
              <MuiSkeleton variant="text" width={96} height={16} />
              <MuiSkeleton variant="text" width={128} height={12} />
            </Stack>
          </Box>
          <MuiSkeleton variant="rounded" width={64} height={24} sx={{ borderRadius: 12 }} />
        </Box>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: 1,
          }}
        >
          <MuiSkeleton variant="rounded" height={32} sx={{ borderRadius: 2 }} />
          <MuiSkeleton variant="rounded" height={32} sx={{ borderRadius: 2 }} />
        </Box>
      </Stack>
    </Box>
  )
}

/**
 * Skeleton for dashboard stats row
 */
export function SkeletonDashboardStats({ sx }: SkeletonProps) {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: {
          xs: '1fr',
          md: 'repeat(2, 1fr)',
          lg: 'repeat(4, 1fr)',
        },
        gap: 2,
        ...sx,
      }}
    >
      {Array.from({ length: 4 }).map((_, i) => (
        <SkeletonStat key={i} />
      ))}
    </Box>
  )
}

/**
 * Skeleton for server grid
 */
export function SkeletonServerGrid({ count = 6, sx }: SkeletonProps & { count?: number }) {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: {
          xs: '1fr',
          md: 'repeat(2, 1fr)',
          lg: 'repeat(3, 1fr)',
        },
        gap: 2,
        ...sx,
      }}
    >
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonServerCard key={i} />
      ))}
    </Box>
  )
}
