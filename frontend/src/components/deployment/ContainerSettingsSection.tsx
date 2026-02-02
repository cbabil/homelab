/**
 * Container Settings Section Component
 *
 * Displays container name and restart policy configuration.
 */

import { Box, Typography, Select, MenuItem } from "@mui/material";
import { Input } from "@/components/ui/Input";
import { DeploymentConfig } from "@/hooks/useDeploymentModal";

interface ContainerSettingsSectionProps {
  appName: string;
  containerName: string;
  restartPolicy: DeploymentConfig["restartPolicy"];
  onContainerNameChange: (name: string) => void;
  onRestartPolicyChange: (policy: DeploymentConfig["restartPolicy"]) => void;
}

export function ContainerSettingsSection({
  appName,
  containerName,
  restartPolicy,
  onContainerNameChange,
  onRestartPolicyChange,
}: ContainerSettingsSectionProps) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
      <Typography variant="caption" fontWeight={500}>
        Container
      </Typography>
      <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1.5 }}>
        <Box>
          <Input
            size="sm"
            label="Name"
            fullWidth
            value={containerName}
            onChange={(e) => onContainerNameChange(e.target.value)}
            placeholder={appName.toLowerCase().replace(/\s+/g, "-")}
            className="text-xs"
          />
        </Box>
        <Box>
          <Typography
            component="label"
            sx={{
              fontSize: "0.875rem",
              fontWeight: 500,
              mb: 0.75,
              display: "block",
            }}
          >
            Restart Policy
          </Typography>
          <Select
            size="small"
            value={restartPolicy || "unless-stopped"}
            onChange={(e) =>
              onRestartPolicyChange(
                e.target.value as DeploymentConfig["restartPolicy"],
              )
            }
            sx={{ fontSize: "0.75rem", height: 32, width: "100%" }}
          >
            <MenuItem value="no">No</MenuItem>
            <MenuItem value="always">Always</MenuItem>
            <MenuItem value="on-failure">On Failure</MenuItem>
            <MenuItem value="unless-stopped">Unless Stopped</MenuItem>
          </Select>
        </Box>
      </Box>
    </Box>
  );
}
