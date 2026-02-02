/**
 * Avatar Handler Hook
 *
 * Handles avatar selection, upload, and removal logic.
 */

import React, { useState, useRef } from "react";
import { useMCP } from "@/providers/MCPProvider";
import { useToast } from "@/components/ui/Toast";
import { useTranslation } from "react-i18next";
import { AUTH_STORAGE_KEYS } from "@/types/auth";
import type { UpdateAvatarResponse, UserProfile } from "./types";
import { MAX_AVATAR_SIZE } from "./types";

function getToken(): string | null {
  return (
    localStorage.getItem(AUTH_STORAGE_KEYS.TOKEN) ||
    sessionStorage.getItem(AUTH_STORAGE_KEYS.TOKEN)
  );
}

interface UseAvatarHandlerParams {
  fetchProfile: () => Promise<void>;
}

export function useAvatarHandler({ fetchProfile }: UseAvatarHandlerParams) {
  const { t } = useTranslation();
  const { client, isConnected } = useMCP();
  const { addToast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);

  const handleAvatarSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      addToast({
        type: "error",
        title: t("profile.invalidFileType"),
        message: t("profile.invalidFileTypeMessage"),
      });
      return;
    }

    if (file.size > MAX_AVATAR_SIZE * 0.75) {
      addToast({
        type: "error",
        title: t("profile.fileTooLarge"),
        message: t("profile.fileTooLargeMessage"),
      });
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target?.result as string;
      setAvatarPreview(dataUrl);
    };
    reader.readAsDataURL(file);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleAvatarUpload = async () => {
    if (!avatarPreview || !isConnected) return;

    const token = getToken();
    if (!token) {
      addToast({
        type: "error",
        title: t("profile.sessionExpired"),
        message: t("profile.sessionExpiredMessage"),
      });
      return;
    }

    setIsUploadingAvatar(true);

    try {
      const response = await client.callTool<UpdateAvatarResponse>(
        "update_avatar",
        { token, avatar: avatarPreview },
      );
      const result = response.data as UpdateAvatarResponse | undefined;

      if (response.success && result?.success) {
        addToast({
          type: "success",
          title: t("profile.avatarUpdated"),
          message: t("profile.avatarUpdatedMessage"),
        });
        await fetchProfile();
      } else {
        addToast({
          type: "error",
          title: t("profile.uploadFailed"),
          message: result?.message || t("profile.failedToUpdateAvatar"),
        });
      }
    } catch (err) {
      addToast({
        type: "error",
        title: t("profile.uploadFailed"),
        message: err instanceof Error ? err.message : t("common.error"),
      });
    } finally {
      setIsUploadingAvatar(false);
    }
  };

  const handleAvatarRemove = async () => {
    if (!isConnected) return;

    const token = getToken();
    if (!token) return;

    setIsUploadingAvatar(true);

    try {
      const response = await client.callTool<UpdateAvatarResponse>(
        "update_avatar",
        { token, avatar: null },
      );
      const result = response.data as UpdateAvatarResponse | undefined;

      if (response.success && result?.success) {
        addToast({
          type: "success",
          title: t("profile.avatarRemoved"),
          message: t("profile.avatarRemovedMessage"),
        });
        setAvatarPreview(null);
        await fetchProfile();
      } else {
        addToast({
          type: "error",
          title: t("profile.removeFailed"),
          message: result?.message || t("profile.failedToRemoveAvatar"),
        });
      }
    } catch (err) {
      addToast({
        type: "error",
        title: t("profile.removeFailed"),
        message: err instanceof Error ? err.message : t("common.error"),
      });
    } finally {
      setIsUploadingAvatar(false);
    }
  };

  const handleCancelPreview = () => {
    setAvatarPreview(null);
  };

  const getDisplayAvatar = (profile: UserProfile | null) =>
    avatarPreview || profile?.avatar;

  return {
    fileInputRef,
    avatarPreview,
    setAvatarPreview,
    isUploadingAvatar,
    handleAvatarSelect,
    handleAvatarUpload,
    handleAvatarRemove,
    handleCancelPreview,
    getDisplayAvatar,
  };
}
