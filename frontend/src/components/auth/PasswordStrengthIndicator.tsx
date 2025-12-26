/**
 * Password Strength Indicator Component
 * 
 * Visual indicator for password strength during registration,
 * helping users create secure passwords.
 */

import { Check, X } from 'lucide-react'
import { PasswordStrength } from '@/types/auth'
import { cn } from '@/utils/cn'

interface PasswordStrengthIndicatorProps {
  strength: PasswordStrength
  password: string
}

export function PasswordStrengthIndicator({ strength, password }: PasswordStrengthIndicatorProps) {
  // Don't show anything if no password entered
  if (!password) {
    return null
  }

  const getStrengthColor = (score: number): string => {
    if (score <= 2) return 'text-red-500'
    if (score <= 3) return 'text-yellow-500'
    if (score <= 4) return 'text-blue-500'
    return 'text-green-500'
  }

  const getStrengthText = (score: number): string => {
    if (score <= 2) return 'Weak'
    if (score <= 3) return 'Fair'
    if (score <= 4) return 'Good'
    return 'Strong'
  }

  const getStrengthBarWidth = (score: number): string => {
    return `${(score / 5) * 100}%`
  }

  return (
    <div className="mt-2 space-y-2">
      {/* Strength Bar */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
          <div 
            className={cn(
              'h-full transition-all duration-300',
              strength.score <= 2 && 'bg-red-500',
              strength.score === 3 && 'bg-yellow-500',
              strength.score === 4 && 'bg-blue-500',
              strength.score === 5 && 'bg-green-500'
            )}
            style={{ width: getStrengthBarWidth(strength.score) }}
          />
        </div>
        <span className={cn('text-sm font-medium', getStrengthColor(strength.score))}>
          {getStrengthText(strength.score)}
        </span>
      </div>

      {/* Requirements Checklist */}
      <div className="grid grid-cols-1 gap-1 text-xs">
        {[
          { key: 'minLength', label: '12+ characters' },
          { key: 'hasUppercase', label: 'Uppercase letter' },
          { key: 'hasLowercase', label: 'Lowercase letter' },
          { key: 'hasNumber', label: 'Number' },
          { key: 'hasSpecialChar', label: 'Special character' }
        ].map(({ key, label }) => {
          const isMet = strength.requirements[key as keyof typeof strength.requirements]
          return (
            <div key={key} className="flex items-center gap-1">
              {isMet ? (
                <Check className="w-3 h-3 text-green-500" />
              ) : (
                <X className="w-3 h-3 text-muted-foreground" />
              )}
              <span className={cn(
                'text-xs',
                isMet ? 'text-green-600' : 'text-muted-foreground'
              )}>
                {label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}