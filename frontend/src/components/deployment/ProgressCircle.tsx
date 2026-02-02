/**
 * Progress Circle Component
 *
 * Circular progress indicator for deployment status.
 */

import { Box, Typography } from "@mui/material";

interface ProgressCircleProps {
  progress: number;
  isComplete: boolean;
  hasError: boolean;
}

export function ProgressCircle({
  progress,
  isComplete,
  hasError,
}: ProgressCircleProps) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        width: 192,
      }}
    >
      <Box sx={{ position: "relative", width: 144, height: 144 }}>
        <svg
          width="144"
          height="144"
          viewBox="0 0 100 100"
          style={{ transform: "rotate(-90deg)" }}
        >
          <circle
            cx="50"
            cy="50"
            r="42"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            style={{ color: "rgba(0,0,0,0.1)" }}
          />
          <circle
            cx="50"
            cy="50"
            r="42"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            strokeLinecap="round"
            style={{
              color: isComplete ? "#10b981" : hasError ? "#ef4444" : "#1976d2",
              strokeDasharray: 264,
              strokeDashoffset: 264 - (264 * progress) / 100,
              transition: "stroke-dashoffset 0.5s ease",
            }}
          />
        </svg>

        <Box
          sx={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Typography
            variant="h3"
            fontWeight={700}
            sx={{
              color: hasError
                ? "error.main"
                : isComplete
                  ? "success.main"
                  : "primary.main",
            }}
          >
            {progress}%
          </Typography>
        </Box>
      </Box>

      <Typography
        variant="body2"
        color="text.secondary"
        textAlign="center"
        sx={{ mt: 4 }}
      >
        {isComplete
          ? "Ready to use"
          : hasError
            ? "Installation failed"
            : "Installing..."}
      </Typography>
    </Box>
  );
}
