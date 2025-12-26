/**
 * Class Name Utility
 * 
 * Utility function for conditionally joining CSS classes.
 * Used with Tailwind CSS and component variants.
 */

import { type ClassValue, clsx } from 'clsx'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}