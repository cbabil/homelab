/**
 * Dashboard Loading State Component
 *
 * Loading skeleton shown while dashboard data is being fetched.
 */

import { Card, Stack, Grid } from '@mui/material'
import { Skeleton } from '@/components/ui/Skeleton'

export function DashboardLoadingState() {
  return (
    <Stack spacing={3}>
      <Stack spacing={1}>
        <Skeleton sx={{ height: 32, width: 192 }} />
        <Skeleton sx={{ height: 16, width: 384 }} />
      </Stack>

      <Grid container spacing={3}>
        {Array.from({ length: 4 }).map((_, i) => (
          <Grid size={{ xs: 12, sm: 6, lg: 3 }} key={i}>
            <Card sx={{ p: 3 }}>
              <Stack spacing={1.5}>
                <Skeleton sx={{ width: 48, height: 48, borderRadius: 1.5 }} />
                <Skeleton sx={{ height: 24, width: 80 }} />
                <Skeleton sx={{ height: 16, width: 128 }} />
              </Stack>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Stack>
  )
}