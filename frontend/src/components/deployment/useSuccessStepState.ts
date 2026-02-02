/**
 * Success Step State Hook
 *
 * Manages state computations for the success step.
 */

import { useMemo, useState, useEffect, useRef } from "react";
import { ServerDeploymentStatus } from "@/hooks/useDeploymentModal";
import { InstallationStatusData } from "@/hooks/useInstallationStatus";

export function useSuccessStepState(
  targetServers: ServerDeploymentStatus[],
  status?: InstallationStatusData | null,
) {
  const overallProgress = useMemo(() => {
    if (targetServers.length === 0) return 0;
    const totalProgress = targetServers.reduce((sum, s) => sum + s.progress, 0);
    return Math.round(totalProgress / targetServers.length);
  }, [targetServers]);

  const completedServers = targetServers.filter(
    (s) => s.status === "running",
  ).length;
  const errorServers = targetServers.filter((s) => s.status === "error").length;
  const isComplete =
    targetServers.length > 0 && completedServers === targetServers.length;
  const hasError = errorServers > 0;

  const currentStatus = useMemo(() => {
    if (targetServers.length > 0) {
      if (isComplete) return "running";
      const statusPriority = [
        "running",
        "error",
        "starting",
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
  }, [targetServers, isComplete, status?.status]);

  const [elapsedTime, setElapsedTime] = useState(0);
  const previousStatus = useRef(currentStatus);

  useEffect(() => {
    if (previousStatus.current !== currentStatus && currentStatus !== "error") {
      setElapsedTime(0);
      previousStatus.current = currentStatus;
    } else if (currentStatus === "error") {
      previousStatus.current = currentStatus;
    }

    if (!isComplete && !hasError) {
      const interval = setInterval(() => {
        setElapsedTime((prev) => prev + 1);
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [currentStatus, isComplete, hasError]);

  const errorAtStep = useMemo(() => {
    if (!hasError) return null;
    if (currentStatus === "pulling" || currentStatus === "pending") {
      return "pulling";
    }
    if (currentStatus === "creating") return "creating";
    if (currentStatus === "starting") return "starting";
    if (currentStatus === "error") return "pulling";
    return null;
  }, [hasError, currentStatus]);

  return {
    overallProgress,
    isComplete,
    hasError,
    currentStatus,
    elapsedTime,
    errorAtStep,
  };
}
