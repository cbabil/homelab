/**
 * Environment Variable Row Component
 *
 * Displays a single environment variable with key/value inputs and delete button.
 */

import { Trash2 } from "lucide-react";
import { Box, Typography, IconButton } from "@mui/material";
import { Input } from "@/components/ui/Input";

export interface EnvVarRowProps {
  envKey: string;
  value: string;
  showKeyInput?: boolean;
  onKeyChange?: (oldKey: string, newKey: string, value: string) => void;
  onValueChange: (key: string, value: string) => void;
  onRemove: (key: string) => void;
}

export function EnvVarRow({
  envKey,
  value,
  showKeyInput,
  onKeyChange,
  onValueChange,
  onRemove,
}: EnvVarRowProps) {
  const isSecret =
    envKey.toLowerCase().includes("password") ||
    envKey.toLowerCase().includes("secret");

  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr 28px",
        gap: 1,
        alignItems: "center",
      }}
    >
      {showKeyInput ? (
        <Input
          size="sm"
          value={envKey}
          onChange={(e) => onKeyChange?.(envKey, e.target.value, value)}
          className="text-xs font-mono"
        />
      ) : (
        <Typography
          component="div"
          sx={{
            fontSize: "0.75rem",
            fontFamily: "monospace",
            color: "text.secondary",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
          title={envKey}
        >
          {envKey}
        </Typography>
      )}
      <Input
        size="sm"
        type={isSecret ? "password" : "text"}
        value={value}
        onChange={(e) => onValueChange(envKey, e.target.value)}
        placeholder="value"
        className={showKeyInput ? "text-xs font-mono" : "text-xs"}
      />
      <IconButton
        size="small"
        onClick={() => onRemove(envKey)}
        className="text-muted-foreground hover:text-destructive"
        sx={{ width: 28, height: 28 }}
      >
        <Trash2 style={{ width: 14, height: 14 }} />
      </IconButton>
    </Box>
  );
}
