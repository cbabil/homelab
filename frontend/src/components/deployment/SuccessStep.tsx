/**
 * Success Step Component
 *
 * Shows deployment completion status with progress and server list.
 */

import { Box, Typography } from "@mui/material";
import { SuccessStepProps } from "./types";
import { ProgressCircle } from "./ProgressCircle";
import { InstallStepItem } from "./InstallStepItem";
import { ServerProgressList } from "./ServerProgressList";
import { useSuccessStepState } from "./useSuccessStepState";
import { useInstallSteps } from "./useInstallSteps";

export function SuccessStep({
  app,
  result: _result,
  status,
  targetServers,
}: SuccessStepProps) {
  const {
    overallProgress,
    isComplete,
    hasError,
    currentStatus,
    elapsedTime,
    errorAtStep,
  } = useSuccessStepState(targetServers, status);

  const installSteps = useInstallSteps({
    app,
    currentStatus,
    hasError,
    errorAtStep,
    status,
  });

  const completedSteps = installSteps.filter((s) => s.completed).length;
  const totalSteps = installSteps.length;

  return (
    <Box sx={{ minHeight: "100%", display: "flex", flexDirection: "column" }}>
      <Box sx={{ flex: 1, display: "flex", gap: 8, minHeight: 0 }}>
        <ProgressCircle
          progress={overallProgress}
          isComplete={isComplete}
          hasError={hasError}
        />

        <Box
          sx={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            minWidth: 0,
          }}
        >
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              mb: 4,
            }}
          >
            <Typography variant="body2" fontWeight={500} color="text.secondary">
              Installation Progress
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {completedSteps}/{totalSteps} steps
            </Typography>
          </Box>

          <Box sx={{ flex: 1 }}>
            {installSteps.map((step, index) => (
              <InstallStepItem
                key={step.id}
                label={step.label}
                description={step.description}
                icon={step.icon}
                completed={step.completed}
                active={step.active}
                error={step.error}
                duration={step.duration}
                elapsedTime={elapsedTime}
                isLast={index === installSteps.length - 1}
              />
            ))}
          </Box>

          {targetServers.length > 0 && (
            <ServerProgressList targetServers={targetServers} />
          )}

          {isComplete && (
            <Typography variant="body2" color="success.main" sx={{ mt: 4 }}>
              {app.name} is now running and ready to use.
            </Typography>
          )}
        </Box>
      </Box>
    </Box>
  );
}
