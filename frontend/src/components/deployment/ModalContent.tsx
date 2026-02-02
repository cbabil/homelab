/**
 * Modal Content Component
 *
 * Main content area for the deployment modal that renders the appropriate step.
 */

import { Box, DialogContent } from "@mui/material";
import { App } from "@/types/app";
import { ServerConnection } from "@/types/server";
import {
  DeploymentStep,
  DeploymentResult,
  ServerDeploymentStatus,
} from "@/hooks/useDeploymentModal";
import { InstallationStatusData } from "@/hooks/useInstallationStatus";
import { SelectServerStep } from "./SelectServerStep";
import { DeployingStep } from "./DeployingStep";
import { SuccessStep } from "./SuccessStep";
import { ErrorStep } from "./ErrorStep";

interface ModalContentProps {
  step: DeploymentStep;
  app: App;
  servers: ServerConnection[];
  selectedServerIds: string[];
  setSelectedServerIds: (ids: string[]) => void;
  hasRequiredConfig: boolean;
  installationStatus?: InstallationStatusData | null;
  targetServers: ServerDeploymentStatus[];
  deploymentResult: DeploymentResult | null;
  error: string | null;
  onRetry: () => void;
  onCleanup?: () => Promise<boolean>;
}

export function ModalContent({
  step,
  app,
  servers,
  selectedServerIds,
  setSelectedServerIds,
  hasRequiredConfig,
  installationStatus,
  targetServers,
  deploymentResult,
  error,
  onRetry,
  onCleanup,
}: ModalContentProps) {
  return (
    <DialogContent
      sx={{
        flex: 1,
        minHeight: 0,
        overflow: "hidden",
        p: 0,
        borderBottom: "none",
      }}
    >
      <Box sx={{ height: "100%", px: 6, py: 4, overflow: "hidden" }}>
        {step === "select" && (
          <SelectServerStep
            servers={servers}
            selectedServerIds={selectedServerIds}
            setSelectedServerIds={setSelectedServerIds}
            hasRequiredConfig={hasRequiredConfig}
          />
        )}

        {step === "deploying" && (
          <DeployingStep
            app={app}
            status={installationStatus}
            targetServers={targetServers}
          />
        )}

        {step === "success" && (
          <SuccessStep
            app={app}
            result={deploymentResult}
            status={installationStatus}
            targetServers={targetServers}
          />
        )}

        {step === "error" && error && (
          <ErrorStep
            error={error}
            onRetry={onRetry}
            onCleanup={onCleanup}
            hasInstallation={!!deploymentResult?.installationId}
          />
        )}
      </Box>
    </DialogContent>
  );
}
