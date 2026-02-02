/**
 * Application Meta Fields Component
 *
 * Form fields for category, tags, author, and license.
 */

import { Stack, Typography, TextField, Select, MenuItem, FormControl, Grid } from '@mui/material'
import { App, AppCategory } from '@/types/app'

interface ApplicationMetaFieldsProps {
  formData: Partial<App>
  onChange: (field: string, value: string | string[]) => void
  onCategoryChange: (category: AppCategory) => void
  categories: AppCategory[]
}

export function ApplicationMetaFields({
  formData,
  onChange,
  onCategoryChange,
  categories
}: ApplicationMetaFieldsProps) {
  const handleCategorySelect = (categoryId: string) => {
    const category = categories.find(cat => cat.id === categoryId)
    if (category) {
      onCategoryChange(category)
    }
  }

  const handleTagsChange = (value: string) => {
    const tags = value.split(',').map(tag => tag.trim()).filter(Boolean)
    onChange('tags', tags)
  }

  return (
    <Stack spacing={1.5}>
      <div>
        <Typography variant="body2" fontWeight={500} sx={{ mb: 0.5 }}>Category</Typography>
        <FormControl fullWidth size="small" required>
          <Select
            value={formData.category?.id || ''}
            onChange={(e) => handleCategorySelect(e.target.value)}
          >
            <MenuItem value="">Select category</MenuItem>
            {categories.map(cat => (
              <MenuItem key={cat.id} value={cat.id}>{cat.name}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </div>

      <div>
        <Typography variant="body2" fontWeight={500} sx={{ mb: 0.5 }}>Tags</Typography>
        <TextField
          type="text"
          size="small"
          fullWidth
          value={formData.tags?.join(', ') || ''}
          onChange={(e) => handleTagsChange(e.target.value)}
          placeholder="web, docker, self-hosted"
        />
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
          Separate tags with commas
        </Typography>
      </div>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Typography variant="body2" fontWeight={500} sx={{ mb: 0.5 }}>Author</Typography>
          <TextField
            type="text"
            size="small"
            fullWidth
            value={formData.author || ''}
            onChange={(e) => onChange('author', e.target.value)}
            placeholder="Author name"
            required
          />
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Typography variant="body2" fontWeight={500} sx={{ mb: 0.5 }}>License</Typography>
          <TextField
            type="text"
            size="small"
            fullWidth
            value={formData.license || ''}
            onChange={(e) => onChange('license', e.target.value)}
            placeholder="MIT, GPL-3.0, etc."
            required
          />
        </Grid>
      </Grid>
    </Stack>
  )
}
