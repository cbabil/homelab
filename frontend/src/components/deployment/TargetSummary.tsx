/**
 * Target Summary Component
 *
 * Displays the target server name and host for deployment.
 */

import { Server } from "lucide-react";
import { Box, Typography } from "@mui/material";

interface TargetSummaryProps {
  serverName: string;
  serverHost: string;
}

export function TargetSummary({ serverName, serverHost }: TargetSummaryProps) {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 1,
        fontSize: "0.875rem",
      }}
    >
      <Server
        style={{
          width: 16,
          height: 16,
          color: "hsl(var(--muted-foreground))",
        }}
      />
      <Typography component="span" fontWeight={500}>
        {serverName}
      </Typography>
      <Typography component="span" color="text.secondary">
        ({serverHost})
      </Typography>
    </Box>
  );
}
