/**
 * Advanced Environment Variables Section Component
 *
 * Displays environment variables with editable keys and add/remove functionality.
 */

import { Plus } from "lucide-react";
import { Box, Typography } from "@mui/material";
import { EnvVarRow } from "./EnvVarRow";

interface AdvancedEnvVarsSectionProps {
  envVars: [string, string][];
  onKeyChange: (oldKey: string, newKey: string, value: string) => void;
  onValueChange: (key: string, value: string) => void;
  onRemove: (key: string) => void;
  onAdd: () => void;
}

export function AdvancedEnvVarsSection({
  envVars,
  onKeyChange,
  onValueChange,
  onRemove,
  onAdd,
}: AdvancedEnvVarsSectionProps) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
      <Typography variant="caption" fontWeight={500}>
        Environment Variables
      </Typography>
      {envVars.length > 0 && (
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 28px",
            gap: 1,
            fontSize: "0.6875rem",
            color: "text.secondary",
          }}
        >
          <span>Key</span>
          <span>Value</span>
          <span></span>
        </Box>
      )}
      {envVars.map(([key, value]) => (
        <EnvVarRow
          key={key}
          envKey={key}
          value={value}
          showKeyInput
          onKeyChange={onKeyChange}
          onValueChange={onValueChange}
          onRemove={onRemove}
        />
      ))}
      <Box
        component="button"
        type="button"
        onClick={onAdd}
        className="text-muted-foreground hover:text-foreground"
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 0.5,
          fontSize: "0.75rem",
          background: "none",
          border: "none",
          cursor: "pointer",
          p: 0,
        }}
      >
        <Plus style={{ width: 14, height: 14 }} /> Add variable
      </Box>
    </Box>
  );
}
