/**
 * Deploying Step Component
 *
 * Shows deployment progress with animated steps.
 */

import { Box, Stack, Typography, CircularProgress, Alert } from "@mui/material";
import { CheckCircle2, Circle } from "lucide-react";
import { DeployingStepProps } from "./types";

export function DeployingStep({
  app,
  status,
  targetServers,
}: DeployingStepProps) {
  const currentStatus = (() => {
    if (targetServers && targetServers.length > 0) {
      const statusPriority = [
        "running",
        "error",
        "creating",
        "pulling",
        "pending",
      ] as const;
      for (const s of statusPriority) {
        if (targetServers.some((server) => server.status === s)) {
          return s;
        }
      }
    }
    return status?.status || "pending";
  })();

  const steps = [
    {
      id: "connect",
      label: "Connecting to server",
      completed: currentStatus !== "pending",
    },
    {
      id: "pulling",
      label: "Pulling Docker image",
      completed: ["creating", "running", "stopped", "error"].includes(
        currentStatus,
      ),
      active: currentStatus === "pulling",
    },
    {
      id: "creating",
      label: "Creating container",
      completed: ["running", "stopped"].includes(currentStatus),
      active: currentStatus === "creating",
    },
    {
      id: "starting",
      label: "Starting application",
      completed: currentStatus === "running",
      active: false,
    },
  ];

  return (
    <Box sx={{ textAlign: "center", py: 8 }}>
      <CircularProgress size={48} sx={{ mb: 4 }} />
      <Typography variant="subtitle1" fontWeight={500} gutterBottom>
        Deploying {app.name}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        This may take a few minutes depending on image size.
      </Typography>
      <Stack
        spacing={2}
        sx={{ mt: 6, textAlign: "left", maxWidth: 320, mx: "auto" }}
      >
        {steps.map((step) => (
          <Box
            key={step.id}
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 2,
              color:
                !step.completed && !step.active ? "text.secondary" : "inherit",
            }}
          >
            {step.completed ? (
              <CheckCircle2
                style={{ width: 16, height: 16, color: "#10b981" }}
              />
            ) : step.active ? (
              <CircularProgress size={16} />
            ) : (
              <Circle style={{ width: 16, height: 16 }} />
            )}
            <Typography variant="body2">{step.label}</Typography>
          </Box>
        ))}
      </Stack>
      {status?.error_message && (
        <Alert severity="error" sx={{ mt: 4 }}>
          {status.error_message}
        </Alert>
      )}
    </Box>
  );
}
