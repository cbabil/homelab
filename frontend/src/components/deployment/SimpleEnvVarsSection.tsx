/**
 * Simple Environment Variables Section Component
 *
 * Displays environment variables in a simple read-only key format.
 */

import { Box, Typography } from "@mui/material";
import { EnvVarRow } from "./EnvVarRow";

interface SimpleEnvVarsSectionProps {
  envVars: [string, string][];
  onValueChange: (key: string, value: string) => void;
  onRemove: (key: string) => void;
}

export function SimpleEnvVarsSection({
  envVars,
  onValueChange,
  onRemove,
}: SimpleEnvVarsSectionProps) {
  if (envVars.length === 0) return null;

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
      <Typography variant="caption" fontWeight={500} color="text.secondary">
        Configuration
      </Typography>
      <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
        {envVars.map(([key, value]) => (
          <EnvVarRow
            key={key}
            envKey={key}
            value={value}
            onValueChange={onValueChange}
            onRemove={onRemove}
          />
        ))}
      </Box>
    </Box>
  );
}
