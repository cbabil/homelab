/**
 * Modal Header Component
 *
 * Header section for the deployment modal with app icon and title.
 */

import { Box, DialogTitle, Typography } from "@mui/material";
import { Package } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { App } from "@/types/app";
import { DeploymentStep } from "@/hooks/useDeploymentModal";

interface ModalHeaderProps {
  app: App;
  step: DeploymentStep;
  onClose: () => void;
  onDeploy: () => void;
  canDeploy: boolean;
  isDeploying: boolean;
}

export function ModalHeader({
  app,
  step,
  onClose,
  onDeploy,
  canDeploy,
  isDeploying,
}: ModalHeaderProps) {
  const title =
    step === "deploying" || step === "success" ? "Deploying" : "Deploy";

  return (
    <DialogTitle
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 3,
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
        {app.icon ? (
          <Box
            component="img"
            src={app.icon}
            alt=""
            sx={{
              width: 32,
              height: 32,
              objectFit: "contain",
              flexShrink: 0,
            }}
          />
        ) : (
          <Package
            style={{
              width: 24,
              height: 24,
              color: "rgba(0,0,0,0.54)",
              flexShrink: 0,
            }}
          />
        )}
        <Typography variant="h6">
          {title} {app.name}
        </Typography>
      </Box>

      {step === "select" && (
        <Box sx={{ display: "flex", gap: 1 }}>
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
            sx={{ fontSize: "0.7rem", py: 0.25, px: 1.5, minHeight: 26 }}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={onDeploy}
            disabled={!canDeploy || isDeploying}
            loading={isDeploying}
            sx={{ fontSize: "0.7rem", py: 0.25, px: 1.5, minHeight: 26 }}
          >
            {isDeploying ? "Deploying..." : "Deploy"}
          </Button>
        </Box>
      )}
    </DialogTitle>
  );
}
