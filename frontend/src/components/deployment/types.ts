/**
 * Deployment Component Types
 *
 * Shared types for deployment modal components.
 */

import { App } from "@/types/app";
import { ServerConnection } from "@/types/server";
import {
  DeploymentStep,
  DeploymentResult,
  ServerDeploymentStatus,
} from "@/hooks/useDeploymentModal";
import { InstallationStatusData } from "@/hooks/useInstallationStatus";

export interface DeploymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  app: App | null;
  servers: ServerConnection[];
  step: DeploymentStep;
  setStep: (step: DeploymentStep) => void;
  selectedServerIds: string[];
  setSelectedServerIds: (ids: string[]) => void;
  isDeploying: boolean;
  error: string | null;
  deploymentResult: DeploymentResult | null;
  onDeploy: () => Promise<boolean>;
  onRetry?: () => Promise<boolean>;
  installationStatus?: InstallationStatusData | null;
  onCleanup?: () => Promise<boolean>;
  targetServerStatuses?: ServerDeploymentStatus[];
}

export interface ServerWithStatus extends ServerConnection {
  isReady: boolean;
  statusLabel: string;
}

export interface SelectServerStepProps {
  servers: ServerConnection[];
  selectedServerIds: string[];
  setSelectedServerIds: (ids: string[]) => void;
  hasRequiredConfig?: boolean;
}

export interface DeployingStepProps {
  app: App;
  status?: InstallationStatusData | null;
  targetServers?: ServerDeploymentStatus[];
}

export interface ServerProgressListProps {
  targetServers: ServerDeploymentStatus[];
}

export interface SuccessStepProps {
  app: App;
  result: DeploymentResult | null;
  status?: InstallationStatusData | null;
  targetServers: ServerDeploymentStatus[];
}

export interface ErrorStepProps {
  error: string;
  onRetry: () => void;
  onCleanup?: () => Promise<boolean>;
  hasInstallation?: boolean;
}
