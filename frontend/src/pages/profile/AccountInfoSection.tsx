/**
 * Account Information Section Component
 *
 * Displays user account details: username, email, role, and member since date.
 */

import React from "react";
import { User, Mail, Shield, Calendar } from "lucide-react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import Chip from "@mui/material/Chip";
import { useTranslation } from "react-i18next";
import { ProfileAvatar } from "./ProfileAvatar";
import type { UserProfile } from "./types";

interface AccountInfoSectionProps {
  displayProfile: UserProfile;
  displayAvatar: string | null | undefined;
  avatarPreview: string | null;
  isUploadingAvatar: boolean;
  hasExistingAvatar: boolean;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  onAvatarSelect: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onAvatarUpload: () => void;
  onAvatarRemove: () => void;
  onCancelPreview: () => void;
}

function formatDate(dateStr: string | undefined, neverLabel: string): string {
  if (!dateStr) return neverLabel;
  try {
    return (
      new Date(dateStr).toLocaleString("en-US", {
        timeZone: "UTC",
        year: "numeric",
        month: "numeric",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit",
        hour12: true,
      }) + " UTC"
    );
  } catch {
    return dateStr;
  }
}

export function AccountInfoSection({
  displayProfile,
  displayAvatar,
  avatarPreview,
  isUploadingAvatar,
  hasExistingAvatar,
  fileInputRef,
  onAvatarSelect,
  onAvatarUpload,
  onAvatarRemove,
  onCancelPreview,
}: AccountInfoSectionProps) {
  const { t } = useTranslation();

  return (
    <Card sx={{ p: 2 }}>
      <Typography
        variant="subtitle2"
        fontWeight={600}
        color="primary"
        sx={{ mb: 2 }}
      >
        {t("profile.accountInformation")}
      </Typography>

      <Box sx={{ display: "flex", alignItems: "flex-start", gap: 3 }}>
        <ProfileAvatar
          displayAvatar={displayAvatar}
          avatarPreview={avatarPreview}
          isUploadingAvatar={isUploadingAvatar}
          hasExistingAvatar={hasExistingAvatar}
          fileInputRef={fileInputRef}
          onAvatarSelect={onAvatarSelect}
          onAvatarUpload={onAvatarUpload}
          onAvatarRemove={onAvatarRemove}
          onCancelPreview={onCancelPreview}
        />

        <Box
          sx={{
            flex: 1,
            display: "grid",
            gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" },
            gap: 2,
          }}
        >
          <Stack spacing={0.5}>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ textTransform: "uppercase", letterSpacing: 1 }}
            >
              {t("auth.username")}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center">
              <User
                size={16}
                style={{ color: "var(--mui-palette-text-secondary)" }}
              />
              <Typography fontWeight={500}>
                {displayProfile.username}
              </Typography>
            </Stack>
          </Stack>

          <Stack spacing={0.5}>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ textTransform: "uppercase", letterSpacing: 1 }}
            >
              {t("auth.email")}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center">
              <Mail
                size={16}
                style={{ color: "var(--mui-palette-text-secondary)" }}
              />
              <Typography fontWeight={500}>
                {displayProfile.email || t("profile.notSet")}
              </Typography>
            </Stack>
          </Stack>

          <Stack spacing={0.5}>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ textTransform: "uppercase", letterSpacing: 1 }}
            >
              {t("profile.role")}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center">
              <Shield
                size={16}
                style={{ color: "var(--mui-palette-text-secondary)" }}
              />
              <Typography fontWeight={500} sx={{ textTransform: "capitalize" }}>
                {displayProfile.role}
              </Typography>
              {displayProfile.role === "admin" && (
                <Chip
                  label={t("profile.fullAccess")}
                  size="small"
                  sx={{
                    height: 20,
                    fontSize: "0.75rem",
                    bgcolor: (theme) => `${theme.palette.primary.main}1a`,
                    color: "primary.main",
                  }}
                />
              )}
            </Stack>
          </Stack>

          <Stack spacing={0.5}>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ textTransform: "uppercase", letterSpacing: 1 }}
            >
              {t("profile.memberSince")}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center">
              <Calendar
                size={16}
                style={{ color: "var(--mui-palette-text-secondary)" }}
              />
              <Typography fontWeight={500}>
                {formatDate(displayProfile.created_at, t("time.never"))}
              </Typography>
            </Stack>
          </Stack>
        </Box>
      </Box>
    </Card>
  );
}
