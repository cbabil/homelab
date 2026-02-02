/**
 * Install Step Item Component
 *
 * Single step in the installation progress stepper.
 */

import { Box, Typography, CircularProgress } from "@mui/material";
import { CheckCircle2, AlertCircle, LucideIcon } from "lucide-react";
import { formatDuration } from "./utils";

interface InstallStepItemProps {
  label: string;
  description: string;
  icon: LucideIcon;
  completed: boolean;
  active: boolean;
  error: boolean;
  duration?: number;
  elapsedTime: number;
  isLast: boolean;
}

export function InstallStepItem({
  label,
  description,
  icon: StepIcon,
  completed,
  active,
  error,
  duration,
  elapsedTime,
  isLast,
}: InstallStepItemProps) {
  return (
    <Box sx={{ position: "relative", display: "flex", gap: 4 }}>
      {/* Left: Icon and connector line */}
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          pt: "25px",
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: 40,
            height: 40,
            borderRadius: "50%",
            flexShrink: 0,
            bgcolor: error
              ? "error.main"
              : completed
                ? "success.main"
                : active
                  ? "primary.main"
                  : "action.disabled",
          }}
        >
          {error ? (
            <AlertCircle style={{ width: 20, height: 20, color: "white" }} />
          ) : completed ? (
            <CheckCircle2 style={{ width: 20, height: 20, color: "white" }} />
          ) : active ? (
            <CircularProgress size={20} sx={{ color: "white" }} />
          ) : (
            <StepIcon
              style={{
                width: 20,
                height: 20,
                color: "rgba(0,0,0,0.38)",
              }}
            />
          )}
        </Box>
        {/* Connector line */}
        {!isLast && (
          <Box
            sx={{
              width: 2,
              flex: 1,
              minHeight: 32,
              mt: 2,
              mb: "-19px",
              bgcolor: error
                ? "error.main"
                : completed
                  ? "success.main"
                  : "action.disabled",
            }}
          />
        )}
      </Box>

      {/* Right: Content */}
      <Box sx={{ flex: 1, pt: "20px", pb: 3 }}>
        <Box
          sx={{
            display: "flex",
            alignItems: "start",
            justifyContent: "space-between",
          }}
        >
          <Box sx={{ flex: 1 }}>
            <Typography
              variant="body2"
              fontWeight={500}
              sx={{
                color: error
                  ? "error.main"
                  : completed
                    ? "success.main"
                    : active
                      ? "text.primary"
                      : "text.secondary",
              }}
            >
              {label}
            </Typography>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ mt: 0.5 }}
            >
              {completed
                ? "Completed"
                : active || error
                  ? description
                  : "Waiting..."}
            </Typography>
          </Box>

          {/* Duration for completed/active/error steps */}
          {(completed || active || error) && (
            <Typography
              variant="caption"
              sx={{
                fontVariantNumeric: "tabular-nums",
                color: error ? "error.main" : "text.secondary",
              }}
            >
              {completed
                ? duration
                  ? formatDuration(duration)
                  : "\u2014"
                : formatDuration(elapsedTime)}
            </Typography>
          )}
        </Box>
      </Box>
    </Box>
  );
}
