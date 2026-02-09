/**
 * Session Warning Component
 *
 * Displays session expiry warnings with configurable actions.
 * Shows countdown and allows session extension or logout.
 */

import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import { Warning, Schedule, Close } from '@mui/icons-material';
import type { Theme } from '@mui/material/styles';
import { SessionWarning as SessionWarningType } from '@/types/auth';

type WarningLevel = SessionWarningType['warningLevel'];

interface SeverityStyle {
  bgcolor: (theme: Theme) => string;
  borderColor: (theme: Theme) => string;
  iconColor: string;
  textColor: (theme: Theme) => string;
  buttonColor: 'error' | 'warning' | 'info';
}

function getSeverityStyle(warningLevel: WarningLevel): SeverityStyle {
  switch (warningLevel) {
    case 'critical':
      return {
        bgcolor: (theme: Theme) =>
          theme.palette.mode === 'dark' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(254, 226, 226, 1)',
        borderColor: (theme: Theme) =>
          theme.palette.mode === 'dark' ? 'rgba(239, 68, 68, 0.5)' : 'rgba(252, 165, 165, 1)',
        iconColor: 'error.main',
        textColor: (theme: Theme) => (theme.palette.mode === 'dark' ? 'error.light' : 'error.dark'),
        buttonColor: 'error',
      };
    case 'warning':
      return {
        bgcolor: (theme: Theme) =>
          theme.palette.mode === 'dark' ? 'rgba(245, 158, 11, 0.1)' : 'rgba(254, 243, 199, 1)',
        borderColor: (theme: Theme) =>
          theme.palette.mode === 'dark' ? 'rgba(245, 158, 11, 0.5)' : 'rgba(252, 211, 77, 1)',
        iconColor: 'warning.main',
        textColor: (theme: Theme) =>
          theme.palette.mode === 'dark' ? 'warning.light' : 'warning.dark',
        buttonColor: 'warning',
      };
    default:
      return {
        bgcolor: (theme: Theme) =>
          theme.palette.mode === 'dark' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(219, 234, 254, 1)',
        borderColor: (theme: Theme) =>
          theme.palette.mode === 'dark' ? 'rgba(59, 130, 246, 0.5)' : 'rgba(147, 197, 253, 1)',
        iconColor: 'info.main',
        textColor: (theme: Theme) => (theme.palette.mode === 'dark' ? 'info.light' : 'info.dark'),
        buttonColor: 'info',
      };
  }
}

function formatTimeRemaining(minutesRemaining: number): string {
  if (minutesRemaining <= 0) {
    return 'Session has expired';
  } else if (minutesRemaining === 1) {
    return '1 minute remaining';
  }
  return `${minutesRemaining} minutes remaining`;
}

interface SessionWarningProps {
  warning: SessionWarningType;
  onExtendSession?: () => void;
  onLogout?: () => void;
  onDismiss?: () => void;
}

export function SessionWarning({
  warning,
  onExtendSession,
  onLogout,
  onDismiss,
}: SessionWarningProps) {
  if (!warning.isShowing) {
    return null;
  }

  const severity = getSeverityStyle(warning.warningLevel);
  const isUrgent = warning.minutesRemaining <= 1;

  return (
    <Paper
      elevation={8}
      sx={{
        position: 'fixed',
        top: 16,
        right: 16,
        maxWidth: 448,
        width: '100%',
        bgcolor: severity.bgcolor,
        borderLeft: 4,
        borderColor: severity.borderColor,
        p: 2,
        zIndex: 9999,
        animation: 'slideInRight 0.3s ease-out',
        '@keyframes slideInRight': {
          '0%': {
            transform: 'translateX(100%)',
            opacity: 0,
          },
          '100%': {
            transform: 'translateX(0)',
            opacity: 1,
          },
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
        <Box sx={{ flexShrink: 0, pt: 0.5 }}>
          {isUrgent ? (
            <Warning sx={{ fontSize: 20, color: severity.iconColor }} />
          ) : (
            <Schedule sx={{ fontSize: 20, color: severity.iconColor }} />
          )}
        </Box>

        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography variant="body2" fontWeight={600} sx={{ color: severity.textColor }}>
            {isUrgent ? 'Session Expired' : 'Session Expiring Soon'}
          </Typography>
          <Typography
            variant="caption"
            sx={{ color: severity.textColor, mt: 0.5, display: 'block' }}
          >
            {formatTimeRemaining(warning.minutesRemaining)}
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1.5 }}>
            {!isUrgent && onExtendSession && (
              <Button
                size="small"
                variant="contained"
                color={severity.buttonColor}
                onClick={onExtendSession}
                sx={{ fontSize: '0.75rem', py: 0.5, px: 1.5 }}
              >
                Extend Session
              </Button>
            )}

            {onLogout && (
              <Button
                size="small"
                variant="outlined"
                onClick={onLogout}
                sx={{
                  fontSize: '0.75rem',
                  py: 0.5,
                  px: 1.5,
                  borderColor: 'grey.400',
                  color: 'text.primary',
                  '&:hover': {
                    borderColor: 'grey.500',
                    bgcolor: 'action.hover',
                  },
                }}
              >
                {isUrgent ? 'Login Again' : 'Logout'}
              </Button>
            )}
          </Box>
        </Box>

        {onDismiss && !isUrgent && (
          <IconButton
            size="small"
            onClick={onDismiss}
            sx={{
              flexShrink: 0,
              color: severity.textColor,
              p: 0.5,
              '&:hover': {
                bgcolor: 'action.hover',
              },
            }}
          >
            <Close sx={{ fontSize: 16 }} />
          </IconButton>
        )}
      </Box>
    </Paper>
  );
}
