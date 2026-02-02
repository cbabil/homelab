/**
 * Profile Data Hook
 *
 * Handles profile fetching and combines avatar/password functionality.
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/providers/AuthProvider";
import { useMCP } from "@/providers/MCPProvider";
import { AUTH_STORAGE_KEYS } from "@/types/auth";
import type { UserProfile, GetCurrentUserResponse } from "./types";
import { useAvatarHandler } from "./useAvatarHandler";
import { usePasswordChange } from "./usePasswordChange";

function getToken(): string | null {
  return (
    localStorage.getItem(AUTH_STORAGE_KEYS.TOKEN) ||
    sessionStorage.getItem(AUTH_STORAGE_KEYS.TOKEN)
  );
}

export function useProfileData() {
  const { user: authUser } = useAuth();
  const { client, isConnected } = useMCP();

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(true);

  const createFallbackProfile = useCallback((): UserProfile | null => {
    if (!authUser) return null;
    return {
      id: authUser.id,
      username: authUser.username,
      email: authUser.email,
      role: authUser.role,
      is_active: authUser.isActive,
      last_login: authUser.lastLogin,
      created_at: authUser.createdAt,
    };
  }, [authUser]);

  const fetchProfile = useCallback(async () => {
    if (!isConnected) return;

    const token = getToken();
    if (!token) {
      setIsLoadingProfile(false);
      return;
    }

    setIsLoadingProfile(true);

    try {
      const response = await client.callTool<GetCurrentUserResponse>(
        "get_current_user",
        { token },
      );
      const result = response.data as GetCurrentUserResponse | undefined;

      if (response.success && result?.success && result?.data?.user) {
        setProfile(result.data.user);
      } else {
        setProfile(createFallbackProfile());
      }
    } catch (err) {
      console.error("Failed to fetch profile:", err);
      setProfile(createFallbackProfile());
    } finally {
      setIsLoadingProfile(false);
    }
  }, [isConnected, client, createFallbackProfile]);

  useEffect(() => {
    if (isConnected && client) {
      fetchProfile();
    } else if (!isConnected && authUser) {
      setIsLoadingProfile(false);
    }
  }, [isConnected, client, authUser, fetchProfile]);

  const avatarHandler = useAvatarHandler({ fetchProfile });
  const passwordHandler = usePasswordChange();

  // Clear avatar preview after profile refresh
  useEffect(() => {
    if (profile) {
      avatarHandler.setAvatarPreview(null);
    }
  }, [profile]);

  const displayProfile =
    profile ||
    (authUser
      ? {
          id: authUser.id,
          username: authUser.username,
          email: authUser.email,
          role: authUser.role,
          is_active: authUser.isActive,
          last_login: authUser.lastLogin,
          created_at: authUser.createdAt,
        }
      : null);

  const displayAvatar = avatarHandler.getDisplayAvatar(profile);

  return {
    // Profile state
    profile,
    displayProfile,
    isLoadingProfile,
    authUser,

    // Avatar state and handlers
    fileInputRef: avatarHandler.fileInputRef,
    avatarPreview: avatarHandler.avatarPreview,
    displayAvatar,
    isUploadingAvatar: avatarHandler.isUploadingAvatar,
    handleAvatarSelect: avatarHandler.handleAvatarSelect,
    handleAvatarUpload: avatarHandler.handleAvatarUpload,
    handleAvatarRemove: avatarHandler.handleAvatarRemove,
    handleCancelPreview: avatarHandler.handleCancelPreview,

    // Password state and handlers (includes isConnected)
    ...passwordHandler,
  };
}
