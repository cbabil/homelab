/**
 * Profile Avatar Component
 *
 * Displays user avatar with upload, preview, and remove functionality.
 */

import React from "react";
import { User, Camera, Trash2 } from "lucide-react";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import CircularProgress from "@mui/material/CircularProgress";
import IconButton from "@mui/material/IconButton";
import Tooltip from "@mui/material/Tooltip";
import { Button } from "@/components/ui/Button";
import { useTranslation } from "react-i18next";

interface ProfileAvatarProps {
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

export function ProfileAvatar({
  displayAvatar,
  avatarPreview,
  isUploadingAvatar,
  hasExistingAvatar,
  fileInputRef,
  onAvatarSelect,
  onAvatarUpload,
  onAvatarRemove,
  onCancelPreview,
}: ProfileAvatarProps) {
  const { t } = useTranslation();

  return (
    <Box sx={{ flexShrink: 0 }}>
      <Box sx={{ position: "relative" }}>
        {displayAvatar ? (
          <Box
            component="img"
            src={displayAvatar}
            alt={t("profile.profileAvatar")}
            sx={{
              width: 80,
              height: 80,
              borderRadius: "50%",
              objectFit: "cover",
              border: (theme) => `2px solid ${theme.palette.primary.main}33`,
            }}
          />
        ) : (
          <Box
            sx={{
              display: "flex",
              width: 80,
              height: 80,
              alignItems: "center",
              justifyContent: "center",
              borderRadius: "50%",
              border: (theme) => `2px solid ${theme.palette.primary.main}`,
              color: "primary.main",
            }}
          >
            <User size={40} />
          </Box>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/gif,image/webp"
          style={{ display: "none" }}
          onChange={onAvatarSelect}
        />

        <Tooltip title={t("profile.changeAvatar")}>
          <IconButton
            size="small"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploadingAvatar}
            sx={{
              position: "absolute",
              bottom: 0,
              right: 0,
              backgroundColor: "primary.main",
              color: "primary.contrastText",
              border: 2,
              borderColor: "background.default",
              "&:hover": { backgroundColor: "primary.dark" },
              width: 28,
              height: 28,
              boxShadow: 1,
            }}
          >
            <Camera style={{ width: 14, height: 14 }} />
          </IconButton>
        </Tooltip>

        {hasExistingAvatar && !avatarPreview && !isUploadingAvatar && (
          <Tooltip title={t("profile.removeAvatar")}>
            <IconButton
              size="small"
              onClick={onAvatarRemove}
              sx={{
                position: "absolute",
                top: -4,
                right: -4,
                backgroundColor: "error.main",
                color: "error.contrastText",
                border: 2,
                borderColor: "background.default",
                "&:hover": { backgroundColor: "error.dark" },
                width: 22,
                height: 22,
                boxShadow: 1,
              }}
            >
              <Trash2 style={{ width: 12, height: 12 }} />
            </IconButton>
          </Tooltip>
        )}

        {isUploadingAvatar && (
          <Box
            sx={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              bgcolor: "rgba(0, 0, 0, 0.5)",
              borderRadius: "50%",
            }}
          >
            <CircularProgress size={24} sx={{ color: "white" }} />
          </Box>
        )}
      </Box>

      {avatarPreview && (
        <Stack
          direction="row"
          spacing={0.5}
          sx={{ mt: 1, justifyContent: "center" }}
        >
          <Button
            size="sm"
            variant="primary"
            onClick={onAvatarUpload}
            disabled={isUploadingAvatar}
          >
            {t("common.save")}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={onCancelPreview}
            disabled={isUploadingAvatar}
          >
            {t("common.cancel")}
          </Button>
        </Stack>
      )}
    </Box>
  );
}
