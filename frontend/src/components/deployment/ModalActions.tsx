/**
 * Modal Actions Component
 *
 * Footer actions for the deployment modal.
 */

import { DialogActions } from "@mui/material";
import { Button } from "@/components/ui/Button";
import {
  DeploymentStep,
  ServerDeploymentStatus,
} from "@/hooks/useDeploymentModal";

interface ModalActionsProps {
  step: DeploymentStep;
  targetServers: ServerDeploymentStatus[];
  onClose: () => void;
  onRetry: () => void;
}

export function ModalActions({
  step,
  targetServers,
  onClose,
  onRetry,
}: ModalActionsProps) {
  if (step === "deploying" || step === "select") {
    return null;
  }

  return (
    <DialogActions sx={{ borderTop: "none", pt: 2 }}>
      {step === "success" && (
        <>
          {targetServers.some((s) => s.status === "error") && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              sx={{ fontSize: "0.7rem", py: 0.25, px: 1.5, minHeight: 26 }}
            >
              Try Again
            </Button>
          )}
          <Button
            variant="primary"
            size="sm"
            onClick={onClose}
            sx={{ fontSize: "0.7rem", py: 0.25, px: 1.5, minHeight: 26 }}
          >
            Done
          </Button>
        </>
      )}

      {step === "error" && (
        <Button
          variant="primary"
          size="sm"
          onClick={onClose}
          sx={{ fontSize: "0.7rem", py: 0.25, px: 1.5, minHeight: 26 }}
        >
          Close
        </Button>
      )}
    </DialogActions>
  );
}
