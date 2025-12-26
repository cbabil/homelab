/**
 * Theme Switcher Component
 *
 * Simplified theme toggle with Moon/Sun icons for light/dark modes.
 * Features smooth animations and professional styling.
 */

import { Sun, Moon } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { useTheme } from '@/providers/ThemeProvider'

export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme()

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light')
  }

  return (
    <Button
      onClick={toggleTheme}
      variant="ghost"
      size="icon"
      title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      {theme === 'light' ? (
        <Moon className="h-4 w-4 text-muted-foreground" />
      ) : (
        <Sun className="h-4 w-4 text-muted-foreground" />
      )}
    </Button>
  )
}