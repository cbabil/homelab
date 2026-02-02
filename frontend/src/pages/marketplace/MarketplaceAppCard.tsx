/**
 * Marketplace App Card Component
 *
 * Clean, minimal card design matching the reference.
 * Shows icon, name, version and colored category.
 */

import React, { useState, useRef } from 'react'
import { createPortal } from 'react-dom'
import { useTranslation } from 'react-i18next'
import { User, Scale, Package, Wrench, Zap, Store } from 'lucide-react'
import { Card, Box, Typography, IconButton } from '@mui/material'
import type { MarketplaceApp } from '@/types/marketplace'


interface MarketplaceAppCardProps {
  app: MarketplaceApp
  onDeploy?: (app: MarketplaceApp) => void
  repoName?: string
}

// Check if a string is a valid image URL
function isValidIconUrl(icon: string | undefined): boolean {
  if (!icon) return false
  return icon.startsWith('http://') || icon.startsWith('https://') || icon.startsWith('data:image/')
}

export function MarketplaceAppCard({ app, onDeploy, repoName }: MarketplaceAppCardProps) {
  const { t } = useTranslation()
  const [showTooltip, setShowTooltip] = useState(false)
  const [tooltipPos, setTooltipPos] = useState({ top: 0, left: 0 })
  const [iconError, setIconError] = useState(false)
  const cardRef = useRef<HTMLDivElement>(null)

  const hasValidIcon = isValidIconUrl(app.icon) && !iconError

  const handleDeploy = (e: React.MouseEvent) => {
    e.stopPropagation()
    e.preventDefault()
    if (onDeploy) {
      onDeploy(app)
    }
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    setTooltipPos({
      top: e.clientY + 15,
      left: Math.min(e.clientX + 15, window.innerWidth - 270)
    })
  }

  const handleMouseEnter = (e: React.MouseEvent) => {
    handleMouseMove(e)
    setShowTooltip(true)
  }

  const handleMouseLeave = () => {
    setShowTooltip(false)
  }

  return (
    <Card
      ref={cardRef}
      elevation={1}
      sx={{
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        height: 90,
        p: 0.75
      }}
    >
      {/* Top right: Deploy button */}
      {onDeploy && (
        <Box sx={{ position: 'absolute', top: 4, right: 8, zIndex: 10 }}>
          <IconButton
            size="small"
            onClick={handleDeploy}
            title={t('marketplace.tooltip.deployToServer')}
            sx={{
              p: 0.25,
              color: 'text.secondary',
              '&:hover': {
                color: 'primary.main'
              }
            }}
          >
            <Zap style={{ width: 12, height: 12 }} />
          </IconButton>
        </Box>
      )}

      {/* Main content - centered vertically */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
        {/* Tooltip trigger area - tight around content */}
        <Box
          sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}
          onMouseEnter={handleMouseEnter}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
        >
          {/* Icon */}
          <Box sx={{ width: 24, height: 24, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {hasValidIcon ? (
              <Box
                component="img"
                src={app.icon}
                alt=""
                sx={{ width: '100%', height: '100%', objectFit: 'contain' }}
                onError={() => setIconError(true)}
                onLoad={(e) => {
                  const img = e.target as HTMLImageElement
                  if (img.naturalWidth === 0) setIconError(true)
                }}
              />
            ) : (
              <Package style={{ width: 12, height: 12, color: 'text.secondary' }} />
            )}
          </Box>

          {/* Name + Version */}
          <Typography
            sx={{ fontSize: 11, fontWeight: 500, textOverflow: 'ellipsis', overflow: 'hidden', maxWidth: '100%', textAlign: 'center', mt: 0.25, px: 0.25, lineHeight: 1.2 }}
          >
            {app.name}
          </Typography>
          <Typography sx={{ fontSize: 9, color: 'text.secondary', lineHeight: 1 }}>
            v{app.version}
          </Typography>
        </Box>
      </Box>

      {/* Category - at bottom */}
      <Typography sx={{ fontSize: 9, color: 'primary.main', textOverflow: 'ellipsis', overflow: 'hidden', maxWidth: '100%' }}>
        {app.category}
      </Typography>

      {/* Tooltip */}
      {showTooltip && createPortal(
        <Box
          sx={{
            position: 'fixed',
            width: 256,
            bgcolor: 'background.paper',
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            boxShadow: 3,
            zIndex: 9999,
            overflow: 'hidden',
            pointerEvents: 'none'
          }}
          style={{ top: tooltipPos.top, left: tooltipPos.left }}
        >
          <Box sx={{ p: 1.5, borderBottom: 1, borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{ width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {hasValidIcon ? (
                  <Box component="img" src={app.icon} alt="" sx={{ width: 32, height: 32, objectFit: 'contain' }} />
                ) : (
                  <Package style={{ width: 20, height: 20, color: 'text.secondary' }} />
                )}
              </Box>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>{app.name}</Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>v{app.version}</Typography>
              </Box>
            </Box>
          </Box>

          <Box sx={{ p: 1.5, display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <User style={{ width: 14, height: 14, color: 'text.secondary' }} />
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>{t('marketplace.tooltip.author')}</Typography>
              <Typography variant="caption" sx={{ ml: 'auto', fontWeight: 500 }}>{app.author || '—'}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Scale style={{ width: 14, height: 14, color: 'text.secondary' }} />
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>{t('marketplace.tooltip.license')}</Typography>
              <Typography variant="caption" sx={{ ml: 'auto', fontWeight: 500 }}>{app.license || '—'}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Wrench style={{ width: 14, height: 14, color: 'text.secondary' }} />
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>{t('marketplace.tooltip.maintainer')}</Typography>
              <Typography variant="caption" sx={{ ml: 'auto', fontWeight: 500 }}>{app.maintainers?.join(', ') || '—'}</Typography>
            </Box>
            {repoName && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Store style={{ width: 14, height: 14, color: 'text.secondary' }} />
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>{t('marketplace.tooltip.source')}</Typography>
                <Typography variant="caption" sx={{ ml: 'auto', fontWeight: 500, textOverflow: 'ellipsis', overflow: 'hidden', maxWidth: 120 }}>
                  {repoName}
                </Typography>
              </Box>
            )}
          </Box>

          {app.description && (
            <Box sx={{ p: 1.5, bgcolor: 'action.hover', borderTop: 1, borderColor: 'divider' }}>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>{app.description}</Typography>
            </Box>
          )}
        </Box>,
        document.body
      )}
    </Card>
  )
}
