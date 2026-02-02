/**
 * Category Grid Component
 *
 * Grid of application categories for filtering.
 */

import { Home } from 'lucide-react'
import { Box, Grid, Stack, Typography } from '@mui/material'
import { Button } from '@/components/ui/Button'
import { AppCategory } from '@/types/app'

interface CategoryGridProps {
  categories: AppCategory[]
  selectedCategory: string | null
  onCategorySelect: (categoryId: string | null) => void
  appCounts: Record<string, number>
  totalApps: number
}

export function CategoryGrid({
  categories,
  selectedCategory,
  onCategorySelect,
  appCounts,
  totalApps
}: CategoryGridProps) {
  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 6, md: 4, lg: 2 }}>
        <Button
          onClick={() => onCategorySelect(null)}
          variant="outline"
          sx={{
            p: 2,
            borderRadius: 3,
            textAlign: 'left',
            height: '100%',
            justifyContent: 'flex-start',
            borderColor: selectedCategory === null ? 'primary.main' : undefined,
            bgcolor: selectedCategory === null ? 'primary.light' : undefined,
            '&:hover': {
              bgcolor: selectedCategory === null ? 'primary.light' : undefined
            }
          }}
        >
          <Stack spacing={1}>
            <Box sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 32,
              height: 32,
              borderRadius: 1,
              bgcolor: 'primary.light'
            }}>
              <Home className="h-5 w-5 text-primary" />
            </Box>
            <Stack spacing={0.5}>
              <Typography variant="body2" fontWeight={500}>All Apps</Typography>
              <Typography variant="caption" color="text.secondary">{totalApps} available</Typography>
            </Stack>
          </Stack>
        </Button>
      </Grid>

      {categories.map((category) => {
        const IconComponent = category.icon
        return (
          <Grid key={category.id} size={{ xs: 6, md: 4, lg: 2 }}>
            <Button
              onClick={() => onCategorySelect(category.id)}
              variant="outline"
              sx={{
                p: 2,
                borderRadius: 3,
                textAlign: 'left',
                height: '100%',
                justifyContent: 'flex-start',
                borderColor: selectedCategory === category.id ? 'primary.main' : undefined,
                bgcolor: selectedCategory === category.id ? 'primary.light' : undefined,
                '&:hover': {
                  bgcolor: selectedCategory === category.id ? 'primary.light' : undefined
                }
              }}
            >
              <Stack spacing={1}>
                <Box sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: 32,
                  height: 32,
                  borderRadius: 1,
                  bgcolor: 'primary.light'
                }}>
                  <IconComponent className="h-5 w-5 text-primary" />
                </Box>
                <Stack spacing={0.5}>
                  <Typography variant="body2" fontWeight={500}>{category.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {appCounts[category.id] || 0} apps
                  </Typography>
                </Stack>
              </Stack>
            </Button>
          </Grid>
        )
      })}
    </Grid>
  )
}