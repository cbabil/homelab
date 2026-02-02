/**
 * Application Header Component
 *
 * Modern header with branding, connection status, and theme switcher.
 * Features gradient background and improved visual hierarchy.
 */

import React, { useState } from 'react'
import { Settings, LogOut, User, ChevronDown, Brush } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Box, Stack, Typography, IconButton, Avatar, SxProps, Theme } from '@mui/material'
import { ThemeSwitcher } from '@/components/ui/ThemeSwitcher'
import { NotificationDropdown } from '@/components/ui/NotificationDropdown'
import { useAuth } from '@/providers/AuthProvider'
import { useToast } from '@/components/ui/Toast'
import { useDataServices } from '@/hooks/useDataServices'
import { clearTomoCaches } from '@/utils/cacheUtils'
import TomoLogo from '../../../../assets/tomo_logo_minimal.png'

interface UserMenuItemProps {
  icon: React.ReactNode
  label: string
  onClick?: () => void
  to?: string
  variant?: 'default' | 'danger'
}

const menuItemBaseSx: SxProps<Theme> = {
  display: 'flex',
  alignItems: 'center',
  gap: 1.5,
  width: '100%',
  px: 1.5,
  py: 1,
  border: 'none',
  bgcolor: 'transparent',
  cursor: 'pointer',
  textDecoration: 'none'
}

function UserMenuItem({ icon, label, onClick, to, variant = 'default' }: UserMenuItemProps) {
  const sx: SxProps<Theme> = {
    ...menuItemBaseSx,
    color: variant === 'danger' ? 'error.main' : 'text.primary',
    '&:hover': { bgcolor: variant === 'danger' ? 'error.lighter' : 'action.hover' }
  }

  if (to) {
    return (
      <Box component={Link} to={to} onClick={onClick} sx={sx}>
        {icon}
        <Typography variant="body2">{label}</Typography>
      </Box>
    )
  }

  return (
    <Box component="button" onClick={onClick} sx={sx}>
      {icon}
      <Typography variant="body2">{label}</Typography>
    </Box>
  )
}

function HeaderBranding() {
  const { t } = useTranslation()

  return (
    <Stack direction="row" alignItems="center" spacing={2}>
      <Stack direction="row" alignItems="center" spacing={1.5}>
        <Box
          component="img"
          src={TomoLogo}
          alt="Tomo Logo"
          sx={{ height: 40, width: 40 }}
        />
        <Stack>
          <Typography
            variant="h6"
            sx={(theme) => ({
              fontWeight: 700,
              letterSpacing: '-0.02em',
              background: `linear-gradient(to right, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            })}
          >
            {t('header.appName')}
          </Typography>
          <Typography variant="caption" color="text.secondary" fontWeight={500}>
            {t('header.edition')}
          </Typography>
        </Stack>
      </Stack>
    </Stack>
  )
}

interface UserMenuButtonProps {
  username: string
  role: string
  isOpen: boolean
  onClick: () => void
}

function UserMenuButton({ username, role, isOpen, onClick }: UserMenuButtonProps) {
  const { t } = useTranslation()

  return (
    <IconButton
      onClick={onClick}
      title={t('header.userMenu')}
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1.5,
        p: 1,
        borderRadius: 2,
        '&:hover': { bgcolor: 'action.hover' }
      }}
    >
      <Avatar
        sx={{
          width: 32,
          height: 32,
          bgcolor: 'primary.main',
          color: 'primary.contrastText'
        }}
      >
        <User className="h-4 w-4" />
      </Avatar>
      <Stack sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'flex-start' }}>
        <Typography variant="body2" fontWeight={500}>
          {username}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'capitalize' }}>
          {role}
        </Typography>
      </Stack>
      <ChevronDown
        style={{
          width: 16,
          height: 16,
          color: 'text.secondary',
          transition: 'transform 0.2s',
          transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)'
        }}
      />
    </IconButton>
  )
}

interface UserMenuDropdownProps {
  user: { username: string; email?: string; role: string; isActive: boolean; lastLogin: string }
  onClose: () => void
  onLogout: () => void
  onClearCache: () => void
}

function UserMenuDropdown({ user, onClose, onLogout, onClearCache }: UserMenuDropdownProps) {
  const { t } = useTranslation()
  const iconStyle = { width: 16, height: 16, color: 'text.secondary' }

  return (
    <>
      <Box sx={{ position: 'fixed', inset: 0, zIndex: 40 }} onClick={onClose} />
      <Box
        sx={{
          position: 'absolute',
          right: 0,
          mt: 1,
          width: 224,
          bgcolor: 'background.paper',
          border: 1,
          borderColor: 'divider',
          borderRadius: 2,
          boxShadow: 3,
          zIndex: 50
        }}
      >
        <Box sx={{ p: 1.5, borderBottom: 1, borderColor: 'divider' }}>
          <Stack direction="row" alignItems="center" spacing={1.5}>
            <Avatar
              sx={{ width: 40, height: 40, bgcolor: 'primary.main', color: 'primary.contrastText' }}
            >
              <User className="h-5 w-5" />
            </Avatar>
            <Stack sx={{ flex: 1, minWidth: 0 }}>
              <Typography variant="body2" fontWeight={500} noWrap>
                {user.username}
              </Typography>
              <Typography variant="caption" color="text.secondary" noWrap>
                {user.email}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'capitalize' }}>
                {user.role} • {user.isActive ? t('header.active') : t('header.inactive')}
              </Typography>
            </Stack>
          </Stack>
        </Box>

        <Box sx={{ py: 0.5 }}>
          <UserMenuItem
            icon={<Brush style={iconStyle} />}
            label={t('header.clearCache')}
            onClick={onClearCache}
          />
          <UserMenuItem
            icon={<User style={iconStyle} />}
            label={t('nav.profile')}
            to="/profile"
            onClick={onClose}
          />
          <UserMenuItem
            icon={<Settings style={iconStyle} />}
            label={t('nav.settings')}
            to="/settings"
            onClick={onClose}
          />
          <UserMenuItem
            icon={<LogOut style={{ width: 16, height: 16 }} />}
            label={t('header.signOut')}
            onClick={onLogout}
            variant="danger"
          />
        </Box>

        <Box sx={{ px: 1.5, py: 1, borderTop: 1, borderColor: 'divider' }}>
          <Typography variant="caption" color="text.secondary">
            {t('header.lastLogin')} {new Date(user.lastLogin).toLocaleDateString()}
          </Typography>
        </Box>
      </Box>
    </>
  )
}

export function Header() {
  const { t } = useTranslation()
  const { user, logout } = useAuth()
  const { factory } = useDataServices()
  const { addToast } = useToast()
  const [showUserMenu, setShowUserMenu] = useState(false)

  const handleLogout = () => {
    logout()
    setShowUserMenu(false)
  }

  const handleClearCache = () => {
    clearTomoCaches()

    try {
      factory.clearDataCaches()
      factory.clearServiceCache()
    } catch (error) {
      console.warn('Failed to clear data service caches', error)
    }

    addToast({
      type: 'success',
      title: t('header.cacheClearedTitle'),
      message: t('header.cacheClearedMessage'),
      duration: 3000
    })

    setShowUserMenu(false)
  }

  return (
    <Box
      component="header"
      sx={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        backdropFilter: 'blur(8px)',
        background:
          'linear-gradient(to right, rgba(var(--background-rgb), 0.6), rgba(var(--background-rgb), 0.8))',
        borderBottom: 1,
        borderColor: 'divider'
      }}
    >
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="space-between"
        sx={{ height: 64, width: '100%', px: 3 }}
      >
        <HeaderBranding />

        <Stack direction="row" alignItems="center" spacing={2}>
          <NotificationDropdown />
          <ThemeSwitcher />

          {user && (
            <Box sx={{ position: 'relative' }}>
              <UserMenuButton
                username={user.username}
                role={user.role}
                isOpen={showUserMenu}
                onClick={() => setShowUserMenu(!showUserMenu)}
              />

              {showUserMenu && (
                <UserMenuDropdown
                  user={user}
                  onClose={() => setShowUserMenu(false)}
                  onLogout={handleLogout}
                  onClearCache={handleClearCache}
                />
              )}
            </Box>
          )}
        </Stack>
      </Stack>
    </Box>
  )
}
