/**
 * Modal Component
 *
 * Reusable modal dialog with customizable size and close behavior.
 * Uses MUI sx props for styling.
 */

import React, { useEffect, useCallback, useRef } from 'react'
import { X } from 'lucide-react'
import { Box, Stack, type SxProps, type Theme } from '@mui/material'
import { Button } from './Button'

// Selector for focusable elements
const FOCUSABLE_SELECTOR = [
  'button:not([disabled])',
  '[href]',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: React.ReactNode
  children: React.ReactNode
  footer?: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  closeOnBackdrop?: boolean
  closeOnEscape?: boolean
  showCloseButton?: boolean
  className?: string
  contentClassName?: string
}

const modalSizes: Record<'sm' | 'md' | 'lg' | 'xl' | 'full', SxProps<Theme>> = {
  sm: { maxWidth: 384 },
  md: { maxWidth: 448 },
  lg: { maxWidth: 672 },
  xl: { maxWidth: 896 },
  full: { maxWidth: '90vw', maxHeight: '90vh' }
}

// Internal sub-components to reduce main function line count
interface ModalHeaderSectionProps {
  title?: React.ReactNode
  showCloseButton: boolean
  onClose: () => void
}

function ModalHeaderSection({ title, showCloseButton, onClose }: ModalHeaderSectionProps) {
  if (!title && !showCloseButton) return null

  return (
    <Stack
      direction="row"
      alignItems="center"
      justifyContent="space-between"
      sx={{
        px: 3,
        py: 2,
        borderBottom: 1,
        borderColor: 'divider',
        flexShrink: 0
      }}
    >
      {title && (
        <Box
          component="h2"
          id="modal-title"
          sx={{ fontSize: '1.125rem', fontWeight: 600 }}
        >
          {title}
        </Box>
      )}
      {showCloseButton && (
        <Button
          onClick={onClose}
          variant="ghost"
          size="icon"
          className="ml-auto"
          aria-label="Close modal"
        >
          <X className="h-5 w-5" />
        </Button>
      )}
    </Stack>
  )
}

interface ModalContentSectionProps {
  children: React.ReactNode
  contentClassName?: string
}

function ModalContentSection({ children, contentClassName }: ModalContentSectionProps) {
  return (
    <Box
      sx={{
        flex: 1,
        overflow: 'hidden',
        px: 3,
        py: 2,
        display: 'flex',
        flexDirection: 'column',
        ...(contentClassName && { className: contentClassName })
      }}
    >
      {children}
    </Box>
  )
}

interface ModalFooterSectionProps {
  footer: React.ReactNode
}

function ModalFooterSection({ footer }: ModalFooterSectionProps) {
  return (
    <Stack
      direction="row"
      alignItems="center"
      justifyContent="flex-end"
      spacing={1.5}
      sx={{
        px: 3,
        py: 2,
        borderTop: 1,
        borderColor: 'divider',
        flexShrink: 0
      }}
    >
      {footer}
    </Stack>
  )
}

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'md',
  closeOnBackdrop = true,
  closeOnEscape = true,
  showCloseButton = true,
  className,
  contentClassName
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null)
  const previousFocusRef = useRef<HTMLElement | null>(null)

  // Handle escape key
  const handleEscape = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape' && closeOnEscape) {
      onClose()
    }
  }, [closeOnEscape, onClose])

  // Handle Tab key for focus trap
  const handleTabKey = useCallback((e: KeyboardEvent) => {
    if (e.key !== 'Tab' || !modalRef.current) return

    const focusableElements = modalRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
    if (focusableElements.length === 0) return

    const firstElement = focusableElements[0]
    const lastElement = focusableElements[focusableElements.length - 1]

    if (e.shiftKey) {
      // Shift+Tab: if on first element, wrap to last
      if (document.activeElement === firstElement) {
        e.preventDefault()
        lastElement.focus()
      }
    } else {
      // Tab: if on last element, wrap to first
      if (document.activeElement === lastElement) {
        e.preventDefault()
        firstElement.focus()
      }
    }
  }, [])

  // Handle backdrop click
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && closeOnBackdrop) {
      onClose()
    }
  }

  // Store previous focus and set up event listeners
  useEffect(() => {
    if (isOpen) {
      // Store the previously focused element
      previousFocusRef.current = document.activeElement as HTMLElement

      document.addEventListener('keydown', handleEscape)
      document.addEventListener('keydown', handleTabKey)
      document.body.style.overflow = 'hidden'

      // Focus first focusable element in modal after render
      requestAnimationFrame(() => {
        if (modalRef.current) {
          const focusableElements = modalRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
          if (focusableElements.length > 0) {
            focusableElements[0].focus()
          } else {
            // If no focusable elements, focus the modal container itself
            modalRef.current.focus()
          }
        }
      })
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.removeEventListener('keydown', handleTabKey)
      document.body.style.overflow = ''

      // Return focus to previously focused element
      if (previousFocusRef.current && typeof previousFocusRef.current.focus === 'function') {
        previousFocusRef.current.focus()
      }
    }
  }, [isOpen, handleEscape, handleTabKey])

  if (!isOpen) return null

  return (
    <Box
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'modal-title' : undefined}
      sx={{
        position: 'fixed',
        inset: 0,
        bgcolor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 50
      }}
    >
      <Box
        ref={modalRef}
        tabIndex={-1}
        sx={{
          bgcolor: 'background.default',
          borderRadius: 3,
          border: 1,
          borderColor: 'divider',
          boxShadow: 3,
          width: '100%',
          mx: 2,
          display: 'flex',
          flexDirection: 'column',
          outline: 'none',
          ...modalSizes[size],
          ...(size === 'full' && { height: '90vh' }),
          ...(className && { className })
        }}
      >
        <ModalHeaderSection title={title} showCloseButton={showCloseButton} onClose={onClose} />
        <ModalContentSection contentClassName={contentClassName}>{children}</ModalContentSection>
        {footer && <ModalFooterSection footer={footer} />}
      </Box>
    </Box>
  )
}

// Convenience components for building modal content
export function ModalHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <Stack
      direction="row"
      alignItems="center"
      spacing={1.5}
      sx={{ mb: 2, ...(className && { className }) }}
    >
      {children}
    </Stack>
  )
}

export function ModalBody({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <Stack spacing={2} sx={className ? { className } : undefined}>
      {children}
    </Stack>
  )
}

export function ModalFooter({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <Stack
      direction="row"
      alignItems="center"
      justifyContent="flex-end"
      spacing={1.5}
      sx={{ pt: 2, ...(className && { className }) }}
    >
      {children}
    </Stack>
  )
}
