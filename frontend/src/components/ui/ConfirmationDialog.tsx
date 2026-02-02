/**
 * Reusable Confirmation Dialog Component
 *
 * A flexible MUI-based confirmation dialog for various actions.
 */

import { useState, useCallback, ReactNode } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box
} from '@mui/material'
import { AlertTriangle } from 'lucide-react'

/**
 * Animated dots component for loading states
 */
function AnimatedDots() {
  return (
    <Box
      component="span"
      sx={{
        '&::after': {
          content: '"..."',
          animation: 'dots 1.5s steps(4, end) infinite',
          display: 'inline-block',
          width: '1.5em',
          textAlign: 'left',
        },
        '@keyframes dots': {
          '0%': { content: '""' },
          '25%': { content: '"."' },
          '50%': { content: '".."' },
          '75%': { content: '"..."' },
          '100%': { content: '""' },
        },
      }}
    />
  )
}

export interface ConfirmationDialogProps {
  open: boolean
  title: string
  message: string
  hint?: string
  icon?: ReactNode
  confirmLabel: string
  confirmingLabel?: string
  cancelLabel?: string
  skipLabel?: string
  confirmColor?: 'error' | 'primary' | 'warning' | 'success'
  onClose: () => void
  onSkip?: () => void
  onConfirm: () => Promise<boolean | void>
}

export function ConfirmationDialog({
  open,
  title,
  message,
  hint,
  icon,
  confirmLabel,
  confirmingLabel,
  cancelLabel = 'Cancel',
  skipLabel,
  confirmColor = 'error',
  onClose,
  onSkip,
  onConfirm
}: ConfirmationDialogProps) {
  const [isProcessing, setIsProcessing] = useState(false)

  const handleConfirm = useCallback(async () => {
    setIsProcessing(true)
    try {
      await onConfirm()
    } finally {
      setIsProcessing(false)
    }
  }, [onConfirm])

  return (
    <Dialog open={open} onClose={isProcessing ? undefined : onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {icon || <AlertTriangle size={20} color="#f59e0b" />}
        {title}
      </DialogTitle>
      <DialogContent>
        <Typography>{message}</Typography>
        {hint && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            {hint}
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button size="small" onClick={onClose} disabled={isProcessing}>
          {cancelLabel}
        </Button>
        {skipLabel && onSkip && (
          <Button size="small" onClick={onSkip} disabled={isProcessing}>
            {skipLabel}
          </Button>
        )}
        <Button
          size="small"
          onClick={handleConfirm}
          color={confirmColor}
          variant="contained"
          disabled={isProcessing}
        >
          {isProcessing ? (
            <>
              {confirmingLabel || confirmLabel}
              <AnimatedDots />
            </>
          ) : confirmLabel}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

/**
 * Hook for managing confirmation dialog state
 */
export interface UseConfirmationDialogOptions<T> {
  onConfirm: (item: T) => Promise<boolean | void>
}

export function useConfirmationDialog<T>({ onConfirm }: UseConfirmationDialogOptions<T>) {
  const [item, setItem] = useState<T | null>(null)

  const openDialog = useCallback((itemToConfirm: T) => {
    setItem(itemToConfirm)
  }, [])

  const closeDialog = useCallback(() => {
    setItem(null)
  }, [])

  const handleConfirm = useCallback(async () => {
    if (item) {
      const result = await onConfirm(item)
      // Close dialog after confirmation completes (unless explicitly returned false)
      if (result !== false) {
        setItem(null)
      }
      return result
    }
  }, [item, onConfirm])

  return {
    isOpen: item !== null,
    item,
    openDialog,
    closeDialog,
    handleConfirm
  }
}
