/**
 * Target Servers Hook
 *
 * Computes target server statuses from selected servers and installation status.
 */

import { useMemo } from "react";
import { ServerConnection } from "@/types/server";
import { ServerDeploymentStatus } from "@/hooks/useDeploymentModal";
import { InstallationStatusData } from "@/hooks/useInstallationStatus";

function getProgressFromStatus(status: string): number {
  switch (status) {
    case "pending":
      return 5;
    case "pulling":
      return 35;
    case "creating":
      return 70;
    case "running":
      return 100;
    default:
      return 0;
  }
}

export function useTargetServers(
  targetServerStatuses: ServerDeploymentStatus[],
  selectedServers: ServerConnection[],
  installationStatus?: InstallationStatusData | null,
): ServerDeploymentStatus[] {
  return useMemo(() => {
    if (targetServerStatuses.length > 0) {
      return targetServerStatuses;
    }
    if (selectedServers.length > 0 && installationStatus) {
      const progress = getProgressFromStatus(installationStatus.status);
      return selectedServers.map((s) => ({
        serverId: s.id,
        serverName: s.name,
        progress,
        status: installationStatus.status as ServerDeploymentStatus["status"],
        error: installationStatus.error_message,
      }));
    }
    if (selectedServers.length > 0) {
      return selectedServers.map((s) => ({
        serverId: s.id,
        serverName: s.name,
        progress: 5,
        status: "pending" as const,
      }));
    }
    return [];
  }, [targetServerStatuses, selectedServers, installationStatus]);
}
