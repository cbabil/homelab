/**
 * Storage Helpers
 * 
 * Utility functions for localStorage operations with JSON export capability.
 */

import { StorageData, STORAGE_KEY, DATA_VERSION } from './storageTypes'

export function loadFromStorage(): StorageData {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored) as StorageData
      if (parsed.version === DATA_VERSION) {
        return parsed
      }
    }
  } catch (error) {
    console.warn('Failed to load server data, using defaults:', error)
  }

  return {
    version: DATA_VERSION,
    servers: [],
    updated_at: new Date().toISOString()
  }
}

export function saveToStorage(data: StorageData): void {
  try {
    const updatedData = {
      ...data,
      updated_at: new Date().toISOString()
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedData))
  } catch (error) {
    console.error('Failed to save server data:', error)
  }
}

export function exportServersAsJSON(data: StorageData): void {
  try {
    const exportData = {
      exported_at: new Date().toISOString(),
      version: data.version,
      servers: data.servers
    }
    
    const dataStr = JSON.stringify(exportData, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    
    const filename = `homelab-servers-${new Date().toISOString().split('T')[0]}.json`
    const url = URL.createObjectURL(dataBlob)
    
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to export server data:', error)
    throw new Error('Failed to export server data')
  }
}

export function importServersFromJSON(file: File): Promise<StorageData> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    
    reader.onload = (event) => {
      try {
        const content = event.target?.result as string
        const importedData = JSON.parse(content)
        
        // Validate the imported data structure
        if (!importedData.servers || !Array.isArray(importedData.servers)) {
          throw new Error('Invalid server data format')
        }
        
        const newData: StorageData = {
          version: DATA_VERSION,
          servers: importedData.servers,
          updated_at: new Date().toISOString()
        }
        
        resolve(newData)
      } catch (error) {
        reject(new Error('Failed to parse server data file'))
      }
    }
    
    reader.onerror = () => {
      reject(new Error('Failed to read file'))
    }
    
    reader.readAsText(file)
  })
}