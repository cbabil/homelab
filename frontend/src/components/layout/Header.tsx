/**
 * Application Header Component
 *
 * Modern header with branding, connection status, and theme switcher.
 * Features gradient background and improved visual hierarchy.
 */

import { Activity, Settings, LogOut, User, ChevronDown, Brush } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useState } from 'react'
import { ThemeSwitcher } from '@/components/ui/ThemeSwitcher'
import { NotificationDropdown } from '@/components/ui/NotificationDropdown'
import { useAuth } from '@/providers/AuthProvider'
import { useToast } from '@/components/ui/Toast'
import { useDataServices } from '@/hooks/useDataServices'
import { clearHomelabCaches } from '@/utils/cacheUtils'
import { Button } from '@/components/ui/Button'

export function Header() {
  const { user, logout } = useAuth()
  const { factory } = useDataServices()
  const { addToast } = useToast()
  const [showUserMenu, setShowUserMenu] = useState(false)

  const handleLogout = () => {
    logout()
    setShowUserMenu(false)
  }

  const handleClearCache = () => {
    clearHomelabCaches()

    try {
      factory.clearDataCaches()
      factory.clearServiceCache()
    } catch (error) {
      console.warn('Failed to clear data service caches', error)
    }

    addToast({
      type: 'success',
      title: 'Cache cleared',
      message: 'Local caches removed. Data will refresh on next load.',
      duration: 3000
    })

    setShowUserMenu(false)
  }

  return (
    <header className="sticky top-0 z-50 header-gradient backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 w-full items-center justify-between px-6">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/70 shadow-lg shadow-primary/20">
              <Activity className="h-6 w-6 text-primary-foreground" />
            </div>
            <div className="flex flex-col">
              <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-primary to-primary/80 bg-clip-text text-transparent">
                Homelab Assistant
              </h1>
              <span className="text-xs text-muted-foreground font-medium">Professional Edition</span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <NotificationDropdown />
          <ThemeSwitcher />
          
          {/* User Menu Dropdown */}
          {user && (
            <div className="relative">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center space-x-3 h-auto p-2"
                title="User Menu"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <User className="h-4 w-4" />
                </div>
                <div className="hidden md:flex flex-col items-start">
                  <span className="text-sm font-medium">{user.username}</span>
                  <span className="text-xs text-muted-foreground capitalize">{user.role}</span>
                </div>
                <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${showUserMenu ? 'rotate-180' : ''}`} />
              </Button>
              
              {/* Dropdown Menu */}
              {showUserMenu && (
                <>
                  <div 
                    className="fixed inset-0 z-40" 
                    onClick={() => setShowUserMenu(false)}
                  />
                  <div className="absolute right-0 mt-2 w-56 bg-card/95 backdrop-blur border border-border/50 rounded-lg shadow-xl z-50">
                    <div className="p-3 border-b border-border/50">
                      <div className="flex items-center space-x-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
                          <User className="h-5 w-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{user.username}</p>
                          <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                          <p className="text-xs text-muted-foreground capitalize">{user.role} • {user.isActive ? 'Active' : 'Inactive'}</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="py-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleClearCache}
                        className="flex items-center space-x-3 w-full justify-start"
                        leftIcon={<Brush className="h-4 w-4 text-muted-foreground" />}
                      >
                        Clear Cache
                      </Button>

                      <Link
                        to="/settings"
                        className="flex items-center space-x-3 px-3 py-2 text-sm hover:bg-accent transition-colors"
                        onClick={() => setShowUserMenu(false)}
                      >
                        <Settings className="h-4 w-4 text-muted-foreground" />
                        <span>Settings</span>
                      </Link>

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleLogout}
                        className="flex items-center space-x-3 w-full justify-start text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/50"
                        leftIcon={<LogOut className="h-4 w-4" />}
                      >
                        Sign Out
                      </Button>
                    </div>
                    
                    <div className="px-3 py-2 border-t border-border/50">
                      <p className="text-xs text-muted-foreground">
                        Last login: {new Date(user.lastLogin).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
