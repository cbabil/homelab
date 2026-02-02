/**
 * Server Progress List Component
 *
 * Shows deployment progress for each target server.
 */

import { useEffect, useRef } from "react";
import { Box, Typography, LinearProgress } from "@mui/material";
import { ServerProgressListProps } from "./types";

export function ServerProgressList({ targetServers }: ServerProgressListProps) {
  const listRef = useRef<HTMLDivElement>(null);
  const activeRef = useRef<HTMLDivElement>(null);

  const activeServerIndex = targetServers.findIndex(
    (s) =>
      s.status !== "pending" && s.status !== "running" && s.status !== "error",
  );

  useEffect(() => {
    if (activeRef.current && listRef.current) {
      activeRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }
  }, [activeServerIndex]);

  const completedCount = targetServers.filter(
    (s) => s.status === "running",
  ).length;

  return (
    <Box
      sx={{
        mt: 4,
        borderRadius: 1,
        border: 1,
        borderColor: "divider",
        overflow: "hidden",
        flexShrink: 0,
      }}
    >
      <Box
        sx={{
          px: 3,
          py: 1.5,
          bgcolor: "action.hover",
          borderBottom: 1,
          borderColor: "divider",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Typography variant="caption" fontWeight={500} color="text.secondary">
          Servers
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {completedCount}/{targetServers.length} complete
        </Typography>
      </Box>
      <Box
        ref={listRef}
        sx={{
          maxHeight: 200,
          overflow: "auto",
          "& > div:not(:last-child)": {
            borderBottom: 1,
            borderColor: "divider",
          },
        }}
      >
        {targetServers.map((server, index) => {
          const isServerComplete = server.status === "running";
          const isServerError = server.status === "error";
          const isServerActive =
            !isServerComplete && !isServerError && server.status !== "pending";
          const isActiveServer = index === activeServerIndex;

          return (
            <Box
              key={server.serverId}
              ref={isActiveServer ? activeRef : null}
              sx={{
                px: 3,
                py: 2.5,
                transition: "background-color 0.2s",
                bgcolor: isServerActive ? "primary.50" : "transparent",
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  mb: 1.5,
                }}
              >
                <Typography
                  variant="body2"
                  fontWeight={500}
                  noWrap
                  sx={{
                    color: isServerComplete
                      ? "success.main"
                      : isServerError
                        ? "error.main"
                        : "inherit",
                  }}
                >
                  {server.serverName}
                </Typography>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ ml: 2, fontVariantNumeric: "tabular-nums" }}
                >
                  {server.progress}%
                </Typography>
              </Box>

              <LinearProgress
                variant={isServerActive ? "indeterminate" : "determinate"}
                value={isServerActive ? undefined : server.progress}
                sx={{
                  height: 8,
                  borderRadius: 1,
                  bgcolor: "action.hover",
                  "& .MuiLinearProgress-bar": {
                    bgcolor: isServerComplete
                      ? "success.main"
                      : isServerError
                        ? "error.main"
                        : isServerActive
                          ? "primary.main"
                          : "action.disabled",
                  },
                }}
              />

              {isServerError && (
                <Typography
                  variant="caption"
                  color="error"
                  sx={{
                    mt: 1,
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                  }}
                  title={server.error || "Deployment failed"}
                >
                  {server.error || "Deployment failed"}
                </Typography>
              )}
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}
