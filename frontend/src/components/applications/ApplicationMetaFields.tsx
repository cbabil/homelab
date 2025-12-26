/**
 * Application Meta Fields Component
 * 
 * Form fields for category, tags, author, and license.
 */

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
    <div className="space-y-3">
      <div>
        <label className="block text-sm font-medium text-foreground mb-1">Category</label>
        <select
          value={formData.category?.id || ''}
          onChange={(e) => handleCategorySelect(e.target.value)}
          className="w-full px-3 py-1.5 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20"
          required
        >
          <option value="">Select category</option>
          {categories.map(cat => (
            <option key={cat.id} value={cat.id}>{cat.name}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground mb-1">Tags</label>
        <input
          type="text"
          value={formData.tags?.join(', ') || ''}
          onChange={(e) => handleTagsChange(e.target.value)}
          className="w-full px-3 py-1.5 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20"
          placeholder="web, docker, self-hosted"
        />
        <p className="text-xs text-muted-foreground mt-1">Separate tags with commas</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-foreground mb-1">Author</label>
          <input
            type="text"
            value={formData.author || ''}
            onChange={(e) => onChange('author', e.target.value)}
            className="w-full px-3 py-1.5 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20"
            placeholder="Author name"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-1">License</label>
          <input
            type="text"
            value={formData.license || ''}
            onChange={(e) => onChange('license', e.target.value)}
            className="w-full px-3 py-1.5 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20"
            placeholder="MIT, GPL-3.0, etc."
            required
          />
        </div>
      </div>
    </div>
  )
}
