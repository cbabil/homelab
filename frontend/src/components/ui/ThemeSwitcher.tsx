/**
 * Theme Switcher Component
 *
 * Simplified theme toggle with Moon/Sun icons for light/dark modes.
 * Features smooth animations and professional styling.
 */

import { Sun, Moon } from 'lucide-react'
import IconButton from '@mui/material/IconButton'
import { useTheme } from '@/providers/ThemeProvider'

export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme()

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light')
  }

  return (
    <IconButton
      onClick={toggleTheme}
      title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
      sx={{
        color: 'text.secondary',
        borderRadius: 2.5,
        width: 36,
        height: 36,
        '&:hover': {
          bgcolor: 'action.hover',
        },
      }}
    >
      {theme === 'light' ? (
        <Moon style={{ width: 16, height: 16 }} />
      ) : (
        <Sun style={{ width: 16, height: 16 }} />
      )}
    </IconButton>
  )
}