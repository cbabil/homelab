/**
 * Error Step Component
 *
 * Shows deployment error with retry and cleanup options.
 */

import { Box, Stack, Typography } from "@mui/material";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { ErrorStepProps } from "./types";

export function ErrorStep({
  error,
  onRetry,
  onCleanup,
  hasInstallation,
}: ErrorStepProps) {
  return (
    <Box sx={{ textAlign: "center", py: 8 }}>
      <AlertCircle
        style={{
          width: 48,
          height: 48,
          margin: "0 auto",
          color: "#ef4444",
          marginBottom: 16,
        }}
      />
      <Typography variant="subtitle1" fontWeight={500} gutterBottom>
        Deployment Failed
      </Typography>
      <Typography variant="body2" color="error" sx={{ mb: 4 }}>
        {error}
      </Typography>
      <Stack direction="row" spacing={2} justifyContent="center">
        {hasInstallation && onCleanup && (
          <Button
            variant="outline"
            size="sm"
            onClick={onCleanup}
            sx={{ fontSize: "0.7rem", py: 0.25, px: 1.5, minHeight: 26 }}
          >
            Clean Up
          </Button>
        )}
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          sx={{ fontSize: "0.7rem", py: 0.25, px: 1.5, minHeight: 26 }}
        >
          Try Again
        </Button>
      </Stack>
    </Box>
  );
}
