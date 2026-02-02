/**
 * Empty Server State Component
 *
 * Displayed when no servers are configured.
 */

import { Box, Typography } from "@mui/material";
import { Server } from "lucide-react";

export function EmptyServerState() {
  return (
    <Box sx={{ textAlign: "center", py: 8 }}>
      <Server
        style={{
          width: 48,
          height: 48,
          margin: "0 auto",
          color: "rgba(0,0,0,0.38)",
          marginBottom: 12,
        }}
      />
      <Typography variant="subtitle1" fontWeight={500} gutterBottom>
        No Servers Configured
      </Typography>
      <Typography variant="body2" color="text.secondary">
        Add a server in the Servers page before deploying applications.
      </Typography>
    </Box>
  );
}
