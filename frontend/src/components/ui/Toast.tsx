/**
 * Toast Notification System
 *
 * Modern toast notifications with variants and auto-dismiss.
 * Features smooth animations and customizable duration.
 */

import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';

interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

interface ToastContextType {
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

const toastIcons = {
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
};

interface ToastItemProps {
  toast: Toast;
  onRemove: (id: string) => void;
}

function ToastItem({ toast, onRemove }: ToastItemProps) {
  const Icon = toastIcons[toast.type];
  const [isOpen, setIsOpen] = React.useState(true);

  const handleClose = React.useCallback(
    (_event?: React.SyntheticEvent | Event, reason?: string) => {
      if (reason === 'clickaway') {
        return;
      }
      setIsOpen(false);
      setTimeout(() => onRemove(toast.id), 300);
    },
    [toast.id, onRemove]
  );

  // Use role="alert" for errors/warnings (more urgent) and role="status" for success/info
  const role = toast.type === 'error' || toast.type === 'warning' ? 'alert' : 'status';

  return (
    <Snackbar
      open={isOpen}
      autoHideDuration={toast.duration || 5000}
      onClose={handleClose}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      sx={{ position: 'relative', mt: 1 }}
    >
      <Alert
        severity={toast.type}
        role={role}
        icon={<Icon style={{ width: 20, height: 20 }} />}
        action={
          <IconButton
            size="small"
            aria-label={`Dismiss ${toast.type} notification: ${toast.title}`}
            onClick={handleClose}
            sx={{ color: 'inherit' }}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        }
        sx={{
          width: '100%',
          maxWidth: 400,
          boxShadow: 3,
        }}
      >
        <AlertTitle sx={{ fontWeight: 600, fontSize: '0.875rem' }}>{toast.title}</AlertTitle>
        {toast.message && <Box sx={{ fontSize: '0.875rem', opacity: 0.9 }}>{toast.message}</Box>}
      </Alert>
    </Snackbar>
  );
}

interface ToastProviderProps {
  children: React.ReactNode;
}

export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = crypto.randomUUID();
    setToasts((prev) => [...prev, { ...toast, id }]);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}

      <Box
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          zIndex: 1400,
          display: 'flex',
          flexDirection: 'column',
          gap: 1,
          pointerEvents: 'none',
          '& > *': {
            pointerEvents: 'auto',
          },
        }}
      >
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onRemove={removeToast} />
        ))}
      </Box>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);

  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }

  return context;
}
