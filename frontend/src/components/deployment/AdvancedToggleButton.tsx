/**
 * Advanced Toggle Button Component
 *
 * Button to show/hide advanced deployment options.
 */

import { Settings2, ChevronDown, ChevronUp } from "lucide-react";
import { Box } from "@mui/material";

interface AdvancedToggleButtonProps {
  showAdvanced: boolean;
  onClick: () => void;
}

export function AdvancedToggleButton({
  showAdvanced,
  onClick,
}: AdvancedToggleButtonProps) {
  return (
    <Box
      component="button"
      type="button"
      onClick={onClick}
      className="text-muted-foreground hover:text-foreground"
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 0.75,
        fontSize: "0.75rem",
        background: "none",
        border: "none",
        cursor: "pointer",
        p: 0,
      }}
    >
      <Settings2 style={{ width: 14, height: 14 }} />
      {showAdvanced ? "Hide" : "Show"} advanced options
      {showAdvanced ? (
        <ChevronUp style={{ width: 12, height: 12 }} />
      ) : (
        <ChevronDown style={{ width: 12, height: 12 }} />
      )}
    </Box>
  );
}
