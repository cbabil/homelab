/**
 * Deployment Configuration Form
 *
 * Simple form showing environment variables from the app's Docker config.
 * Advanced options toggle reveals full Docker configuration.
 */

import { useState } from "react";
import { Box, Typography } from "@mui/material";
import { App } from "@/types/app";
import { ServerConnection } from "@/types/server";
import { DeploymentConfig } from "@/hooks/useDeploymentModal";
import { TargetSummary } from "./TargetSummary";
import { SimpleEnvVarsSection } from "./SimpleEnvVarsSection";
import { AdvancedToggleButton } from "./AdvancedToggleButton";
import { PortsSection } from "./PortsSection";
import { AdvancedEnvVarsSection } from "./AdvancedEnvVarsSection";
import { ContainerSettingsSection } from "./ContainerSettingsSection";

interface DeploymentConfigFormProps {
  app: App;
  server: ServerConnection;
  config: DeploymentConfig;
  updateConfig: (updates: Partial<DeploymentConfig>) => void;
}

export function DeploymentConfigForm({
  app,
  server,
  config,
  updateConfig,
}: DeploymentConfigFormProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const envVars = Object.entries(config.env || {});
  const hasEnvVars = envVars.length > 0;

  const handleEnvChange = (key: string, value: string) => {
    updateConfig({ env: { ...config.env, [key]: value } });
  };

  const handleEnvKeyChange = (
    oldKey: string,
    newKey: string,
    value: string,
  ) => {
    const newEnv = { ...config.env };
    delete newEnv[oldKey];
    newEnv[newKey] = value;
    updateConfig({ env: newEnv });
  };

  const handleAddEnvVar = () => {
    updateConfig({ env: { ...config.env, [`NEW_VAR_${Date.now()}`]: "" } });
  };

  const handleRemoveEnvVar = (key: string) => {
    const newEnv = { ...config.env };
    delete newEnv[key];
    updateConfig({ env: newEnv });
  };

  const handlePortChange = (containerPort: string, hostPort: string) => {
    updateConfig({
      ports: {
        ...config.ports,
        [containerPort]: parseInt(hostPort) || parseInt(containerPort),
      },
    });
  };

  const requiredPorts = app.requirements?.requiredPorts || [];
  const ports = requiredPorts.map((port) => ({
    containerPort: String(port),
    hostPort: config.ports?.[String(port)]?.toString() || String(port),
  }));

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <TargetSummary serverName={server.name} serverHost={server.host} />

      {hasEnvVars && !showAdvanced && (
        <SimpleEnvVarsSection
          envVars={envVars}
          onValueChange={handleEnvChange}
          onRemove={handleRemoveEnvVar}
        />
      )}

      {!hasEnvVars && !showAdvanced && (
        <Typography
          sx={{
            fontSize: "0.875rem",
            color: "text.secondary",
            textAlign: "center",
            py: 2,
          }}
        >
          No configuration required. Click Deploy to continue.
        </Typography>
      )}

      <AdvancedToggleButton
        showAdvanced={showAdvanced}
        onClick={() => setShowAdvanced(!showAdvanced)}
      />

      {showAdvanced && (
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 2,
            pt: 1,
            borderTop: 1,
            borderColor: "divider",
          }}
        >
          <PortsSection ports={ports} onPortChange={handlePortChange} />

          <AdvancedEnvVarsSection
            envVars={envVars}
            onKeyChange={handleEnvKeyChange}
            onValueChange={handleEnvChange}
            onRemove={handleRemoveEnvVar}
            onAdd={handleAddEnvVar}
          />

          <ContainerSettingsSection
            appName={app.name}
            containerName={config.containerName || ""}
            restartPolicy={config.restartPolicy}
            onContainerNameChange={(name) =>
              updateConfig({ containerName: name })
            }
            onRestartPolicyChange={(policy) =>
              updateConfig({ restartPolicy: policy })
            }
          />
        </Box>
      )}
    </Box>
  );
}
