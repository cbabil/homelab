/**
 * Ports Section Component
 *
 * Displays container-to-host port mappings for deployment configuration.
 */

import { ArrowRight } from "lucide-react";
import { Box, Typography } from "@mui/material";
import { Input } from "@/components/ui/Input";

export interface PortMapping {
  containerPort: string;
  hostPort: string;
}

interface PortsSectionProps {
  ports: PortMapping[];
  onPortChange: (containerPort: string, hostPort: string) => void;
}

export function PortsSection({ ports, onPortChange }: PortsSectionProps) {
  if (ports.length === 0) return null;

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
      <Typography variant="caption" fontWeight={500}>
        Ports
      </Typography>
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "1fr auto 1fr",
          gap: 1.5,
          fontSize: "0.6875rem",
          color: "text.secondary",
        }}
      >
        <span>Container</span>
        <span></span>
        <span>Host</span>
      </Box>
      {ports.map((port) => (
        <Box
          key={port.containerPort}
          sx={{
            display: "grid",
            gridTemplateColumns: "1fr auto 1fr",
            gap: 1.5,
            alignItems: "center",
          }}
        >
          <Input
            size="sm"
            value={port.containerPort}
            disabled
            className="text-xs text-center bg-muted"
          />
          <ArrowRight
            style={{
              width: 12,
              height: 12,
              color: "hsl(var(--muted-foreground))",
            }}
          />
          <Input
            size="sm"
            type="number"
            value={port.hostPort}
            onChange={(e) => onPortChange(port.containerPort, e.target.value)}
            className="text-xs text-center"
          />
        </Box>
      ))}
    </Box>
  );
}
