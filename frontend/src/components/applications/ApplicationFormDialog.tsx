/**
 * Application Form Dialog Component
 *
 * Modal dialog for adding custom applications to the marketplace.
 */

import React from 'react'
import { X } from 'lucide-react'
import { App, AppCategory } from '@/types/app'
import { ApplicationNameFields } from './ApplicationNameFields'
import { ApplicationMetaFields } from './ApplicationMetaFields'
import { RequirementsSection } from './RequirementsSection'
import { useAppForm } from '@/hooks/useAppForm'
import { Button } from '@/components/ui/Button'

interface ApplicationFormDialogProps {
  isOpen: boolean
  onClose: () => void
  onSave: (app: Partial<App>) => void
  app?: App
  title: string
  categories: AppCategory[]
}

export function ApplicationFormDialog({ 
  isOpen, 
  onClose, 
  onSave, 
  app, 
  title,
  categories
}: ApplicationFormDialogProps) {
  const {
    formData,
    handleInputChange,
    handleCategoryChange,
    handleRequirementsChange
  } = useAppForm(app)

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave(formData)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background p-3 rounded-xl border max-w-4xl w-full mx-4">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-semibold text-foreground">{title}</h2>
          <Button
            onClick={onClose}
            variant="ghost"
            size="icon"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <ApplicationNameFields
            formData={formData}
            onChange={handleInputChange}
          />

          <ApplicationMetaFields
            formData={formData}
            onChange={handleInputChange}
            onCategoryChange={handleCategoryChange}
            categories={categories}
          />

          <RequirementsSection
            requirements={formData.requirements || {}}
            onChange={handleRequirementsChange}
          />

          <div className="flex justify-end space-x-3 pt-2 border-t">
            <Button
              type="button"
              onClick={onClose}
              variant="outline"
              size="sm"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
            >
              {app ? 'Update App' : 'Add App'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
