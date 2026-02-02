/**
 * Profile Page Component
 *
 * User profile page displaying account information.
 * Account data is fetched fresh from the database (not JWT cache).
 *
 * Features:
 * - Avatar upload and management
 * - Account information display
 * - Password change with security features
 */

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import { useTranslation } from "react-i18next";
import { useProfileData } from "./useProfileData";
import { AccountInfoSection } from "./AccountInfoSection";
import { ChangePasswordSection } from "./ChangePasswordSection";

export function ProfilePage() {
  const { t } = useTranslation();
  const {
    // Profile state
    profile,
    displayProfile,
    isLoadingProfile,
    authUser,
    isConnected,

    // Avatar state and handlers
    fileInputRef,
    avatarPreview,
    displayAvatar,
    isUploadingAvatar,
    handleAvatarSelect,
    handleAvatarUpload,
    handleAvatarRemove,
    handleCancelPreview,

    // Password state and handlers
    currentPassword,
    setCurrentPassword,
    newPassword,
    setNewPassword,
    confirmPassword,
    setConfirmPassword,
    showCurrentPassword,
    setShowCurrentPassword,
    showNewPassword,
    setShowNewPassword,
    showConfirmPassword,
    setShowConfirmPassword,
    isChangingPassword,
    handlePasswordChange,
  } = useProfileData();

  if (isLoadingProfile) {
    return (
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (!profile && !authUser) {
    return (
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
        }}
      >
        <Typography color="text.secondary">
          {t("profile.unableToLoadProfile")}
        </Typography>
      </Box>
    );
  }

  if (!displayProfile) return null;

  return (
    <Box
      sx={{ height: "100%", display: "flex", flexDirection: "column", gap: 3 }}
    >
      <Box>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          {t("profile.title")}
        </Typography>
        <Typography color="text.secondary">{t("profile.subtitle")}</Typography>
      </Box>

      <Box
        sx={{
          flex: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 2,
        }}
      >
        <AccountInfoSection
          displayProfile={displayProfile}
          displayAvatar={displayAvatar}
          avatarPreview={avatarPreview}
          isUploadingAvatar={isUploadingAvatar}
          hasExistingAvatar={!!profile?.avatar}
          fileInputRef={fileInputRef}
          onAvatarSelect={handleAvatarSelect}
          onAvatarUpload={handleAvatarUpload}
          onAvatarRemove={handleAvatarRemove}
          onCancelPreview={handleCancelPreview}
        />

        <ChangePasswordSection
          currentPassword={currentPassword}
          newPassword={newPassword}
          confirmPassword={confirmPassword}
          showCurrentPassword={showCurrentPassword}
          showNewPassword={showNewPassword}
          showConfirmPassword={showConfirmPassword}
          isChangingPassword={isChangingPassword}
          isConnected={isConnected}
          onCurrentPasswordChange={setCurrentPassword}
          onNewPasswordChange={setNewPassword}
          onConfirmPasswordChange={setConfirmPassword}
          onToggleCurrentPassword={() =>
            setShowCurrentPassword(!showCurrentPassword)
          }
          onToggleNewPassword={() => setShowNewPassword(!showNewPassword)}
          onToggleConfirmPassword={() =>
            setShowConfirmPassword(!showConfirmPassword)
          }
          onSubmit={handlePasswordChange}
        />
      </Box>
    </Box>
  );
}
