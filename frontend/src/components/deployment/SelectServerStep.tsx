/**
 * Select Server Step Component
 *
 * Server selection step for the deployment modal.
 */

import { useMemo, useState, useEffect, useRef } from "react";
import { Box, Typography, Alert } from "@mui/material";
import { AlertTriangle } from "lucide-react";
import { SearchInput } from "@/components/ui/SearchInput";
import { DataTable } from "@/components/ui/DataTable";
import { TablePagination } from "@/components/ui/TablePagination";
import { useDynamicRowCount } from "@/hooks/useDynamicRowCount";
import { SelectServerStepProps, ServerWithStatus } from "./types";
import { getServerColumns, sortServers } from "./ServerTableColumns";
import { EmptyServerState } from "./EmptyServerState";

export function SelectServerStep({
  servers,
  selectedServerIds,
  setSelectedServerIds,
  hasRequiredConfig,
}: SelectServerStepProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(
    new Set(selectedServerIds),
  );
  const containerRef = useRef<HTMLDivElement>(null);

  const itemsPerPage = useDynamicRowCount(containerRef, {
    rowHeight: 32,
    headerHeight: 40,
    paginationHeight: 0,
  });

  useEffect(() => {
    setSelectedIds(new Set(selectedServerIds));
  }, [selectedServerIds]);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, itemsPerPage]);

  const serversWithStatus = useMemo((): ServerWithStatus[] => {
    return servers.map((s) => ({
      ...s,
      isReady: s.status === "connected" && s.docker_installed,
      statusLabel:
        s.status !== "connected"
          ? "Offline"
          : !s.docker_installed
            ? "No Docker"
            : "Ready",
    }));
  }, [servers]);

  const filteredServers = useMemo(() => {
    if (!searchQuery.trim()) return serversWithStatus;
    const query = searchQuery.toLowerCase();
    return serversWithStatus.filter(
      (s) =>
        s.name.toLowerCase().includes(query) ||
        s.host.toLowerCase().includes(query),
    );
  }, [serversWithStatus, searchQuery]);

  const totalPages = Math.ceil(filteredServers.length / itemsPerPage);
  const paginatedServers = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredServers.slice(start, start + itemsPerPage);
  }, [filteredServers, currentPage, itemsPerPage]);

  const handleToggleServer = (server: ServerWithStatus) => {
    if (!server.isReady) return;
    const newSelected = new Set(selectedIds);
    if (newSelected.has(server.id)) {
      newSelected.delete(server.id);
    } else {
      newSelected.add(server.id);
    }
    setSelectedIds(newSelected);
    setSelectedServerIds(Array.from(newSelected));
  };

  const readyCount = serversWithStatus.filter((s) => s.isReady).length;
  const columns = getServerColumns({
    selectedIds,
    onToggleServer: handleToggleServer,
  });

  if (servers.length === 0) {
    return <EmptyServerState />;
  }

  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      {hasRequiredConfig && (
        <Alert severity="warning" icon={<AlertTriangle size={16} />}>
          <Typography variant="body2" fontWeight={500}>
            Configuration required
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
            This app needs configuration after deployment. You can set it up in
            the Applications page.
          </Typography>
        </Alert>
      )}

      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 4,
        }}
      >
        <Box sx={{ flexShrink: 0 }}>
          <Typography variant="subtitle1" fontWeight={500}>
            Select Target Server
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {readyCount} of {servers.length} server
            {servers.length !== 1 ? "s" : ""} ready
          </Typography>
        </Box>
        <SearchInput
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search..."
        />
      </Box>

      <Box sx={{ mt: 3, mb: 2 }} />

      <Box
        ref={containerRef}
        sx={{ flex: 1, minHeight: 0, overflow: "hidden" }}
      >
        <DataTable
          data={paginatedServers}
          columns={columns}
          keyExtractor={(server) => server.id}
          onRowClick={handleToggleServer}
          emptyTitle="No servers found"
          emptyMessage={`No servers match "${searchQuery}"`}
          defaultSortField="name"
          defaultSortDirection="asc"
          sortFn={sortServers}
        />
      </Box>

      <TablePagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
      />
    </Box>
  );
}
