/**
 * Install Steps Hook
 *
 * Computes install step states based on deployment status.
 */

import { useMemo } from "react";
import { Download, Play, Package, LucideIcon } from "lucide-react";
import { InstallationStatusData } from "@/hooks/useInstallationStatus";
import { App } from "@/types/app";

export interface InstallStep {
  id: string;
  label: string;
  description: string;
  icon: LucideIcon;
  completed: boolean;
  active: boolean;
  error: boolean;
  duration?: number;
}

interface UseInstallStepsOptions {
  app: App;
  currentStatus: string;
  hasError: boolean;
  errorAtStep: string | null;
  status?: InstallationStatusData | null;
}

export function useInstallSteps({
  app,
  currentStatus,
  hasError,
  errorAtStep,
  status,
}: UseInstallStepsOptions): InstallStep[] {
  return useMemo(() => {
    return [
      {
        id: "pulling",
        label: "Pulling Docker Image",
        description: `Downloading ${app.name} from registry...`,
        icon: Download,
        completed:
          !hasError &&
          ["creating", "starting", "running", "stopped"].includes(
            currentStatus,
          ),
        active:
          !hasError &&
          (currentStatus === "pulling" || currentStatus === "pending"),
        error: errorAtStep === "pulling",
        duration: ["creating", "starting", "running", "stopped"].includes(
          currentStatus,
        )
          ? status?.step_durations?.pulling
          : undefined,
      },
      {
        id: "creating",
        label: "Creating Container",
        description: "Setting up container with configuration...",
        icon: Package,
        completed:
          !hasError &&
          ["starting", "running", "stopped"].includes(currentStatus),
        active: !hasError && currentStatus === "creating",
        error: errorAtStep === "creating",
        duration: ["starting", "running", "stopped"].includes(currentStatus)
          ? status?.step_durations?.creating
          : undefined,
      },
      {
        id: "starting",
        label: "Starting Application",
        description: "Launching and verifying health...",
        icon: Play,
        completed: !hasError && currentStatus === "running",
        active: !hasError && currentStatus === "starting",
        error: errorAtStep === "starting",
        duration:
          currentStatus === "running"
            ? status?.step_durations?.starting
            : undefined,
      },
    ];
  }, [app.name, currentStatus, hasError, errorAtStep, status]);
}
