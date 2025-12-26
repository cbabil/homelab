/**
 * Application Form Hook
 * 
 * Custom hook for managing application form state and validation.
 */

import { useState, useEffect } from 'react'
import { App, AppCategory, AppRequirements } from '@/types/app'

interface AppFormData extends Partial<App> {
  requirements: AppRequirements
}

export function useAppForm(initialApp?: App) {
  const [formData, setFormData] = useState<AppFormData>({
    name: '',
    description: '',
    version: '',
    category: undefined,
    tags: [],
    author: '',
    license: '',
    requirements: {},
    ...initialApp
  })

  useEffect(() => {
    if (initialApp) {
      setFormData({
        ...initialApp,
        requirements: initialApp.requirements || {}
      })
    }
  }, [initialApp])

  const handleInputChange = (field: string, value: string | string[]) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleCategoryChange = (category: AppCategory) => {
    setFormData(prev => ({
      ...prev,
      category
    }))
  }

  const handleRequirementsChange = (field: string, value: string | string[] | number[]) => {
    setFormData(prev => ({
      ...prev,
      requirements: {
        ...prev.requirements,
        [field]: value
      }
    }))
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      version: '',
      category: undefined,
      tags: [],
      author: '',
      license: '',
      requirements: {}
    })
  }

  const validateForm = (): boolean => {
    return !!(
      formData.name &&
      formData.description &&
      formData.version &&
      formData.category &&
      formData.author &&
      formData.license
    )
  }

  return {
    formData,
    handleInputChange,
    handleCategoryChange,
    handleRequirementsChange,
    resetForm,
    validateForm,
    isValid: validateForm()
  }
}