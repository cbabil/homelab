/**
 * Server Table Columns
 *
 * Column definitions for the server selection table.
 */

import { Typography, Checkbox } from "@mui/material";
import { ColumnDef } from "@/components/ui/DataTable";
import { ServerWithStatus } from "./types";

interface ColumnOptions {
  selectedIds: Set<string>;
  onToggleServer: (server: ServerWithStatus) => void;
}

export function getServerColumns({
  selectedIds,
  onToggleServer,
}: ColumnOptions): ColumnDef<ServerWithStatus>[] {
  return [
    {
      id: "name",
      header: "Name",
      width: "25%",
      sortable: true,
      render: (server) => (
        <Typography
          variant="body2"
          fontWeight={500}
          noWrap
          color={selectedIds.has(server.id) ? "primary" : "inherit"}
          sx={{ opacity: server.isReady ? 1 : 0.4 }}
        >
          {server.name}
        </Typography>
      ),
    },
    {
      id: "system",
      header: "System",
      width: "25%",
      align: "center",
      render: (server) => (
        <Typography
          variant="body2"
          color="text.secondary"
          noWrap
          sx={{ opacity: server.isReady ? 1 : 0.4 }}
        >
          {server.system_info?.os || "\u2014"}{" "}
          {server.system_info?.architecture || ""}
        </Typography>
      ),
    },
    {
      id: "host",
      header: "Host",
      width: "20%",
      align: "center",
      sortable: true,
      render: (server) => (
        <Typography
          variant="body2"
          color="text.secondary"
          noWrap
          sx={{ opacity: server.isReady ? 1 : 0.4 }}
        >
          {server.host}
        </Typography>
      ),
    },
    {
      id: "status",
      header: "Status",
      width: "15%",
      sortable: true,
      render: (server) => (
        <Typography
          variant="body2"
          sx={{
            opacity: server.isReady ? 1 : 0.4,
            color:
              server.statusLabel === "Ready"
                ? "success.main"
                : server.statusLabel === "No Docker"
                  ? "warning.main"
                  : "error.main",
          }}
        >
          {server.statusLabel}
        </Typography>
      ),
    },
    {
      id: "select",
      header: "",
      width: 40,
      align: "right",
      render: (server) => (
        <Checkbox
          size="small"
          checked={selectedIds.has(server.id)}
          disabled={!server.isReady}
          onClick={(e) => e.stopPropagation()}
          onChange={() => onToggleServer(server)}
          sx={{ p: 0 }}
        />
      ),
    },
  ];
}

export function sortServers(
  a: ServerWithStatus,
  b: ServerWithStatus,
  field: string,
  direction: "asc" | "desc",
): number {
  let comparison = 0;
  switch (field) {
    case "name":
      comparison = a.name.localeCompare(b.name);
      break;
    case "host":
      comparison = a.host.localeCompare(b.host);
      break;
    case "status": {
      const statusOrder = { Ready: 0, "No Docker": 1, Offline: 2 };
      comparison =
        statusOrder[a.statusLabel as keyof typeof statusOrder] -
        statusOrder[b.statusLabel as keyof typeof statusOrder];
      break;
    }
  }
  return direction === "asc" ? comparison : -comparison;
}
