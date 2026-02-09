/**
 * Deployment Modal Component
 *
 * Simplified deployment modal: Select Server -> Deploy
 * Configuration happens post-deployment via app management.
 */

import { useMemo } from 'react';
import { Dialog } from '@mui/material';
import { DeploymentModalProps } from './types';
import { ModalHeader } from './ModalHeader';
import { ModalContent } from './ModalContent';
import { ModalActions } from './ModalActions';
import { useTargetServers } from './useTargetServers';

export function DeploymentModal({
  isOpen,
  onClose,
  app,
  servers,
  step,
  setStep,
  selectedServerIds,
  setSelectedServerIds,
  isDeploying,
  error,
  deploymentResult,
  onDeploy,
  onRetry,
  installationStatus,
  onCleanup,
  targetServerStatuses = [],
}: DeploymentModalProps) {
  const selectedServers = useMemo(
    () => servers.filter((s) => selectedServerIds.includes(s.id)),
    [servers, selectedServerIds]
  );

  const targetServers = useTargetServers(targetServerStatuses, selectedServers, installationStatus);

  const hasRequiredConfig = false;

  const canDeploy =
    selectedServerIds.length > 0 &&
    selectedServers.every((s) => s.status === 'connected' && s.docker_installed);

  const handleDeploy = async () => {
    await onDeploy();
  };

  const handleRetry = async () => {
    if (onRetry) {
      await onRetry();
    } else {
      setStep('select');
    }
  };

  if (!app) return null;

  return (
    <Dialog
      open={isOpen}
      onClose={step !== 'deploying' ? onClose : undefined}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          maxWidth: 896,
          height: '80vh',
          maxHeight: 700,
          display: 'flex',
          flexDirection: 'column',
        },
      }}
    >
      <ModalHeader
        app={app}
        step={step}
        onClose={onClose}
        onDeploy={handleDeploy}
        canDeploy={canDeploy}
        isDeploying={isDeploying}
      />

      <ModalContent
        step={step}
        app={app}
        servers={servers}
        selectedServerIds={selectedServerIds}
        setSelectedServerIds={setSelectedServerIds}
        hasRequiredConfig={hasRequiredConfig}
        installationStatus={installationStatus}
        targetServers={targetServers}
        deploymentResult={deploymentResult}
        error={error}
        onRetry={handleRetry}
        onCleanup={onCleanup}
      />

      <ModalActions
        step={step}
        targetServers={targetServers}
        onClose={onClose}
        onRetry={handleRetry}
      />
    </Dialog>
  );
}
